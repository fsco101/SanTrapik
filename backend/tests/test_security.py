import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.middleware.rate_limit import RateLimitMiddleware
from backend.app.services.telemetry import telemetry_service
from backend.app.services.incident_consensus import consensus_engine
from backend.app.services.decay_worker import decay_worker
from datetime import datetime, timezone, timedelta

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_state():
    """Reset rate limiter and telemetry state before each test."""
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, type) and issubclass(middleware.cls, RateLimitMiddleware):
            pass
    # Reset in-memory rate limits
    app.middleware_stack = app.build_middleware_stack()
    telemetry_service._live_incidents.clear()

# -------------------------------------------------------------------------
# 1. Geographic Bounding Box Enforcement & Input Sanitization
# -------------------------------------------------------------------------

def test_incident_out_of_bounds_rejected():
    """Verify coordinates outside Metro Manila boundaries are rejected with HTTP 422."""
    # Latitude outside (Cebu lat 10.31)
    payload = {
        "incident_type": "ACCIDENT",
        "severity": "HIGH",
        "lat": 10.3157,
        "lng": 121.0500,
        "description": "Accident in Cebu should fail"
    }
    resp = client.post("/api/v1/incidents", json=payload)
    assert resp.status_code == 422
    assert "boundaries" in resp.text.lower() or "value_error" in resp.text.lower()

    # Longitude outside (Tokyo lng 139.69)
    payload["lat"] = 14.5800
    payload["lng"] = 139.6917
    resp = client.post("/api/v1/incidents", json=payload)
    assert resp.status_code == 422

def test_incident_xss_sanitization():
    """Verify HTML tags and malicious script payloads are stripped from incident description."""
    payload = {
        "incident_type": "ACCIDENT",
        "severity": "HIGH",
        "lat": 14.5800,
        "lng": 121.0500,
        "description": "<script>alert('pwned')</script>Two sedans collided on EDSA outer lane <b>bold</b>"
    }
    resp = client.post("/api/v1/incidents", json=payload)
    assert resp.status_code in [200, 201]
    data = resp.json()["data"]
    assert "<script>" not in data["description"]
    assert "alert('pwned')" in data["description"]
    assert "<b>" not in data["description"]
    assert "Two sedans collided on EDSA" in data["description"]

def test_incident_invalid_type_rejected():
    """Verify non-standard incident types return HTTP 422."""
    payload = {
        "incident_type": "ALIEN_INVASION",
        "severity": "HIGH",
        "lat": 14.5800,
        "lng": 121.0500,
        "description": "Alien spaceship blocking road"
    }
    resp = client.post("/api/v1/incidents", json=payload)
    assert resp.status_code == 422

# -------------------------------------------------------------------------
# 2. Spatiotemporal Clustering & Consensus Engine
# -------------------------------------------------------------------------

def test_spatiotemporal_clustering_corroboration():
    """
    Verify that a second report within 150m and 15 mins clusters into the existing incident,
    increments report count, bumps confidence, and elevates status from REPORTED to VERIFIED.
    """
    # 1. First commuter reports accident on EDSA near Ortigas
    report1 = {
        "incident_type": "ACCIDENT",
        "severity": "HIGH",
        "lat": 14.5860,
        "lng": 121.0580,
        "description": "Stalled bus blocking 2 lanes",
        "data_source": "COMMUTER_REPORT"
    }
    resp1 = client.post("/api/v1/incidents", json=report1)
    assert resp1.status_code in [200, 201]
    created = resp1.json()["data"]
    inc_id = created["id"]
    assert created["status"] == "REPORTED"
    assert created["report_count"] == 1
    assert created["confidence"] <= 0.50
    assert created["reporter_token"] is not None

    # 2. Second commuter reports the same bottleneck 50 meters away
    # ~50m offset in latitude (0.0004 deg lat ~ 44 meters)
    report2 = {
        "incident_type": "ACCIDENT",
        "severity": "HIGH",
        "lat": 14.5864,
        "lng": 121.0580,
        "description": "Heavy traffic due to bus breakdown",
        "data_source": "COMMUTER_REPORT"
    }
    resp2 = client.post("/api/v1/incidents", json=report2)
    assert resp2.status_code in [200, 201]
    corroborated = resp2.json()["data"]

    # Should have clustered into the same incident ID!
    assert corroborated["id"] == inc_id
    assert corroborated["report_count"] == 2
    assert corroborated["status"] == "VERIFIED"
    assert corroborated["confidence"] >= 0.60

# -------------------------------------------------------------------------
# 3. Protected Incident Resolution & Anti-Griefing
# -------------------------------------------------------------------------

def test_protected_resolution_by_author_token():
    """Verify that only the author with X-Reporter-Token or Admin can resolve directly."""
    report = {
        "incident_type": "STALLED_VEHICLE",
        "severity": "MEDIUM",
        "lat": 14.5500,
        "lng": 121.0250,
        "description": "Stalled taxi on Makati arterial"
    }
    create_resp = client.post("/api/v1/incidents", json=report)
    assert create_resp.status_code in [200, 201]
    inc = create_resp.json()["data"]
    inc_id = inc["id"]
    token = inc["reporter_token"]

    # 1. Unauthorized resolve attempt without token -> HTTP 403
    unauth_resp = client.patch(f"/api/v1/incidents/{inc_id}/resolve")
    assert unauth_resp.status_code == 403
    assert "Unauthorized" in unauth_resp.json()["detail"]

    # 2. Wrong token resolve attempt -> HTTP 403
    wrong_resp = client.patch(
        f"/api/v1/incidents/{inc_id}/resolve",
        headers={"X-Reporter-Token": "invalid_fake_token_12345"}
    )
    assert wrong_resp.status_code == 403

    # 3. Authorized author resolve attempt with valid token -> HTTP 200
    auth_resp = client.patch(
        f"/api/v1/incidents/{inc_id}/resolve",
        headers={"X-Reporter-Token": token}
    )
    assert auth_resp.status_code == 200
    assert auth_resp.json()["data"]["status"] == "RESOLVED"

# -------------------------------------------------------------------------
# 4. Community Clearance Voting Consensus
# -------------------------------------------------------------------------

def test_community_clearance_voting():
    """Verify that community clearance voting moves status to CLEARING and then RESOLVED."""
    report = {
        "incident_type": "ROADWORK",
        "severity": "MEDIUM",
        "lat": 14.6500,
        "lng": 121.0500,
        "description": "Lane repair on Quezon City avenue"
    }
    create_resp = client.post("/api/v1/incidents", json=report)
    inc_id = create_resp.json()["data"]["id"]

    # Vote 1: CLEARED
    v1 = client.post(f"/api/v1/incidents/{inc_id}/vote-clearance", json={"vote": "CLEARED"})
    assert v1.status_code == 200
    assert v1.json()["data"]["cleared_votes"] == 1

    # Vote 2: CLEARED -> status becomes CLEARING
    v2 = client.post(f"/api/v1/incidents/{inc_id}/vote-clearance", json={"vote": "CLEARED"})
    assert v2.status_code == 200
    assert v2.json()["data"]["status"] == "CLEARING"

    # Vote 3: STILL_THERE -> net score drops back down
    v3 = client.post(f"/api/v1/incidents/{inc_id}/vote-clearance", json={"vote": "STILL_THERE"})
    assert v3.status_code == 200
    assert v3.json()["data"]["still_there_votes"] == 1

    # 2 more CLEARED votes -> net score reaches +3 -> RESOLVED!
    client.post(f"/api/v1/incidents/{inc_id}/vote-clearance", json={"vote": "CLEARED"})
    v5 = client.post(f"/api/v1/incidents/{inc_id}/vote-clearance", json={"vote": "CLEARED"})
    assert v5.status_code == 200
    assert v5.json()["data"]["status"] == "RESOLVED"

# -------------------------------------------------------------------------
# 5. Half-Life Decay & Stale Incident Garbage Collection
# -------------------------------------------------------------------------

def test_incident_confidence_decay_and_expiry():
    """Verify that uncorroborated incidents naturally decay and expire after 30+ minutes."""
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(minutes=45)

    stale_inc = {
        "id": "inc_decay_test_01",
        "incident_type": "HAZARD",
        "status": "REPORTED",
        "confidence": 0.35,
        "report_count": 1,
        "reported_at": old_time.isoformat(),
        "last_corroborated_at": old_time.isoformat(),
        "point_lng_lat": [121.0500, 14.5800]
    }

    # Run decay on stale incident
    decay_worker.apply_decay_to_incident(stale_inc, now)
    assert stale_inc["confidence"] < 0.15
    assert stale_inc["status"] == "EXPIRED"

# -------------------------------------------------------------------------
# 6. Sliding Window Rate Limiting Enforcement
# -------------------------------------------------------------------------

def test_incident_rate_limiting():
    """Verify that submitting more than 5 reports within 10 minutes returns HTTP 429."""
    valid_report = {
        "incident_type": "ACCIDENT",
        "severity": "LOW",
        "lat": 14.6000,
        "lng": 121.0500,
        "description": "Minor traffic obstruction"
    }

    # First 5 should succeed (or cluster)
    responses = [client.post("/api/v1/incidents", json=valid_report) for _ in range(5)]
    for r in responses:
        assert r.status_code in [201, 200]

    # The 6th request from same client should be rate-limited
    sixth = client.post("/api/v1/incidents", json=valid_report)
    assert sixth.status_code == 429
    assert sixth.json()["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in sixth.headers
