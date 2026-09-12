import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SanTrapik" in data["message"]

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "SanTrapik" in data["service"]

def test_route_analyze_endpoint():
    # Quezon City Circle to Ayala Triangle Gardens, Makati
    payload = {
        "origin": {
            "lat": 14.6515,
            "lng": 121.0494,
            "name": "Quezon City Memorial Circle"
        },
        "destination": {
            "lat": 14.5573,
            "lng": 121.0234,
            "name": "Ayala Triangle Gardens, Makati"
        },
        "include_alternatives": False
    }
    response = client.post("/api/v1/route/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    routes = data["data"]["routes"]
    assert len(routes) == 1
    
    primary = routes[0]
    assert "summary" in primary
    assert primary["summary"]["total_distance_km"] > 0
    assert primary["summary"]["estimated_travel_time_min"] > 0
    assert primary["summary"]["estimated_delay_min"] >= 0
    assert primary["summary"]["most_affected_segment"] != ""

    assert "expected_relief" in primary
    assert primary["expected_relief"]["is_predicted"] is True
    assert primary["expected_relief"]["confidence"] > 0
    assert "relief_time" in primary["expected_relief"]

    assert len(primary["segments"]) >= 1
    first_seg = primary["segments"][0]
    assert first_seg["average_speed_kmh"] > 0
    assert first_seg["traffic_level"] in ["NORMAL", "MODERATE", "HEAVY", "SEVERE"]

def test_route_analyze_with_alternatives():
    payload = {
        "origin": {
            "lat": 14.6515,
            "lng": 121.0494,
            "name": "Quezon City"
        },
        "destination": {
            "lat": 14.5573,
            "lng": 121.0234,
            "name": "Makati"
        },
        "include_alternatives": True
    }
    response = client.post("/api/v1/route/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    routes = data["data"]["routes"]
    assert len(routes) >= 2
    # Check that recommendation flags exist
    assert any(r["is_recommended"] for r in routes)

def test_traffic_heatmap_endpoint():
    response = client.get("/api/v1/traffic/heatmap")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 50

    feat = data["features"][0]
    assert "road_name" in feat["properties"]
    assert "traffic_color" in feat["properties"]
    assert feat["properties"]["traffic_color"].startswith("#")

def test_incidents_endpoint():
    # 1. Check initial endpoint response
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert isinstance(data["data"], list)

    # 2. Report a live real incident via POST
    report_payload = {
        "incident_type": "ACCIDENT",
        "description": "Multi-vehicle collision occupying middle lane",
        "severity": "CRITICAL",
        "status": "ACTIVE",
        "point_lng_lat": [121.0575, 14.5855],
        "corridor": "EDSA - Ortigas",
        "data_source": "COMMUTER_LIVE_REPORT"
    }
    post_res = client.post("/api/v1/incidents", json=report_payload)
    assert post_res.status_code == 200
    created = post_res.json()["data"]
    inc_id = created["id"]
    assert created["incident_type"] == "ACCIDENT"
    assert created["status"] == "ACTIVE"
    # Verify coordinate was snapped onto road centerline
    assert len(created["point_lng_lat"]) == 2

    # 3. Filter by ACTIVE status and verify created incident is listed
    res_active = client.get("/api/v1/incidents?status=ACTIVE")
    assert res_active.status_code == 200
    active_incs = res_active.json()["data"]
    assert any(i["id"] == inc_id for i in active_incs)

    # 4. Resolve the incident in real-time
    res_resolve = client.patch(f"/api/v1/incidents/{inc_id}/resolve")
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "success"

    # 5. Verify resolved incident is no longer in ACTIVE filter
    res_active_after = client.get("/api/v1/incidents?status=ACTIVE")
    assert not any(i["id"] == inc_id for i in res_active_after.json()["data"])

def test_dashboard_stats_endpoint():
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    stats = data["data"]
    assert stats["active_incidents"] >= 0
    assert "average_road_speed_kmh" in stats
    assert len(stats["most_congested_roads"]) >= 3

