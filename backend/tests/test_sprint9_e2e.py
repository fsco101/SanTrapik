"""
End-to-end integration test verifying all Sprint 9 acceptance criteria (SP9-001 to SP9-005).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_sprint9_full_pipeline_e2e():
    """Verify route analysis returns quantile relief, incident clearance, and spillover warnings."""
    payload = {
        "origin": {"lat": 14.5547, "lng": 121.0244, "name": "Makati CBD"},
        "destination": {"lat": 14.5869, "lng": 121.0614, "name": "Ortigas Center"},
        "include_alternatives": True,
        "transport_mode": "car",
        "use_expressway": True,
    }

    resp = client.post("/api/v1/route/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert len(data["routes"]) > 0
    route = data["routes"][0]

    # 1. SP9-002 Quantile Envelopes verification
    relief = route["expected_relief"]
    assert relief["is_predicted"] is True
    assert "p10_optimistic_mins" in relief
    assert "p50_median_mins" in relief
    assert "p90_pessimistic_mins" in relief
    assert "relief_window_display" in relief
    assert relief["p10_optimistic_mins"] <= relief["p50_median_mins"] <= relief["p90_pessimistic_mins"]
    assert relief["p10_optimistic_mins"] >= 5

    # 2. SP9-003 Spillover Warnings & Segments verification
    assert "spillover_warnings" in route
    assert "spillover_segments" in route

    # 3. SP9-001 Incident Clearance verification
    for seg in route["segments"]:
        for inc in seg["incidents"]:
            assert "clearance_minutes" in inc
            assert "confidence_score" in inc
            assert "tow_dispatch_status" in inc
            if inc["clearance_minutes"] is not None:
                assert inc["clearance_minutes"] >= 5

    # 4. SP9-004 MLOps Circuit Breaker & Health verification
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert "ml_inference" in health_data
    assert health_data["ml_inference"]["status"] in ("OPERATIONAL", "DEGRADED", "FALLBACK")

    status_resp = client.get("/api/v1/ml/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] in ("OPERATIONAL", "DEGRADED", "FALLBACK")
    assert "rolling_mae_minutes" in status_data
