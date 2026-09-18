import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.services.streaming import stream_manager, METERS_PER_DEG_LAT, METERS_PER_DEG_LNG

client = TestClient(app)

def test_speed_deltas_endpoint():
    """Verify GET /api/v1/traffic/speed-deltas returns concise delta records."""
    response = client.get("/api/v1/traffic/speed-deltas")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    first = data["data"][0]
    assert "segment_id" in first
    assert "road_name" in first
    assert "current_speed_kmh" in first
    assert "traffic_level" in first
    assert "traffic_color" in first

def test_invalid_bbox_validation():
    """Partial or inverted bbox parameters must return HTTP 422."""
    # 1. Partial parameters
    resp1 = client.get("/api/v1/telemetry/stream?min_lng=121.0&min_lat=14.5")
    assert resp1.status_code == 422

    # 2. Inverted bounds
    resp2 = client.get("/api/v1/telemetry/stream?min_lng=121.2&min_lat=14.6&max_lng=121.0&max_lat=14.5")
    assert resp2.status_code == 422

@pytest.mark.asyncio
async def test_viewport_bbox_filtering():
    """Verify that clients only receive incident updates if within their visible viewport."""
    # Subscriber QC: Quezon City viewport
    sub_qc = await stream_manager.register_subscriber(
        client_id="sub_qc_test",
        bbox=(121.00, 14.62, 121.08, 14.70)
    )

    # Subscriber Makati: Makati viewport
    sub_makati = await stream_manager.register_subscriber(
        client_id="sub_makati_test",
        bbox=(121.00, 14.52, 121.06, 14.58)
    )

    try:
        # Broadcast incident in Quezon City (14.65, 121.04)
        qc_incident = {
            "id": "inc_test_qc",
            "lat": 14.65,
            "lng": 121.04,
            "incident_type": "ACCIDENT",
            "severity": "HIGH",
            "corridor": "Commonwealth Ave",
            "description": "Multi-vehicle collision near Philcoa"
        }
        await stream_manager.broadcast_incident(qc_incident)

        # QC subscriber MUST receive the event
        assert not sub_qc.queue.empty()
        event_qc = await sub_qc.queue.get()
        assert event_qc["event"] == "incident_update"
        assert event_qc["data"]["id"] == "inc_test_qc"

        # Makati subscriber must NOT receive the event (bandwidth reduction)
        assert sub_makati.queue.empty()

    finally:
        await stream_manager.deregister_subscriber("sub_qc_test")
        await stream_manager.deregister_subscriber("sub_makati_test")

@pytest.mark.asyncio
async def test_route_buffer_obstruction_alert():
    """Verify that an incident within 100m of an active route triggers route_obstruction."""
    route_id = "rt_test_edsa_corridor"
    # Vertical line along longitude 121.04 from latitude 14.55 to 14.65
    coords = [
        [121.0400, 14.5500],
        [121.0400, 14.6000],
        [121.0400, 14.6500]
    ]
    stream_manager.register_route(route_id, coords)

    sub_commuter = await stream_manager.register_subscriber(
        client_id="commuter_edsa_user",
        route_id=route_id
    )

    try:
        # Case A: Incident directly on route (~21m away from 121.0400 at Manila latitude)
        # 0.0002 deg lng ~ 21.5 meters
        near_incident = {
            "id": "inc_chokepoint_direct",
            "lat": 14.5800,
            "lng": 121.0402,
            "incident_type": "ACCIDENT",
            "severity": "CRITICAL",
            "corridor": "EDSA Ortigas Flyover",
            "description": "Bus breakdown blocking middle lanes"
        }
        await stream_manager.broadcast_incident(near_incident)

        # Subscriber must receive both route_obstruction and general incident_update
        events_received = []
        while not sub_commuter.queue.empty():
            events_received.append(await sub_commuter.queue.get())

        event_types = [e["event"] for e in events_received]
        assert "route_obstruction" in event_types
        assert "incident_update" in event_types

        obstruction_event = next(e for e in events_received if e["event"] == "route_obstruction")
        alert_data = obstruction_event["data"]
        assert alert_data["route_id"] == route_id
        assert alert_data["distance_to_route_meters"] <= 100.0
        assert alert_data["estimated_delay_minutes"] >= 15
        assert alert_data["can_reroute"] is True

        # Case B: Incident far away from corridor (~600m away, 0.006 deg lng)
        far_incident = {
            "id": "inc_distant_hazard",
            "lat": 14.5800,
            "lng": 121.0460,
            "incident_type": "ROADWORK",
            "severity": "LOW",
            "corridor": "Side Street",
            "description": "Manhole repair"
        }
        await stream_manager.broadcast_incident(far_incident)

        far_events = []
        while not sub_commuter.queue.empty():
            far_events.append(await sub_commuter.queue.get())

        far_types = [e["event"] for e in far_events]
        # Only general incident_update, NO route_obstruction!
        assert "route_obstruction" not in far_types
        assert "incident_update" in far_types

    finally:
        await stream_manager.deregister_subscriber("commuter_edsa_user")

@pytest.mark.asyncio
async def test_subscription_renegotiation():
    """Verify that client can dynamically update viewport and route via POST endpoint."""
    sub = await stream_manager.register_subscriber(client_id="dynamic_client_1")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        update_payload = {
            "min_lng": 120.95,
            "min_lat": 14.50,
            "max_lng": 121.10,
            "max_lat": 14.65,
            "route_id": "rt_new_corridor"
        }
        res = await ac.post("/api/v1/telemetry/stream/dynamic_client_1/subscription", json=update_payload)
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "success"
        assert json_data["data"]["route_id"] == "rt_new_corridor"

        # Check in memory
        assert sub.bbox == (120.95, 14.50, 121.10, 14.65)
        assert sub.route_id == "rt_new_corridor"

    await stream_manager.deregister_subscriber("dynamic_client_1")
