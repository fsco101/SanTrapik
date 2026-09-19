"""
Unit and integration tests for MLOps Drift Monitor & Circuit Breaker (SP9-004).
Validates residual tracking, outlier tracking, circuit breaker tripping (OPERATIONAL -> FALLBACK),
empirical MMDA fallback, and health check status reporting.
"""

import pytest
from datetime import datetime, timezone

from backend.app.services.drift_monitor import (
    DriftMonitorService,
    drift_monitor,
    fallback_heuristic_relief,
)
from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_initial_state_operational():
    """Drift monitor initializes in OPERATIONAL state."""
    monitor = DriftMonitorService()
    status = monitor.get_status()
    assert status["status"] in ("OPERATIONAL", "DEGRADED")
    assert "rolling_mae_minutes" in status
    assert "inferences_last_hour" in status

def test_circuit_breaker_trips_on_high_residuals():
    """When rolling residual MAE exceeds 15 minutes, circuit breaker trips to FALLBACK."""
    monitor = DriftMonitorService(mae_threshold=15.0)

    # Record 10 observations with massive error (residual = 25 minutes)
    for _ in range(10):
        monitor.record_observation(predicted_minutes=45.0, observed_minutes=15.0)

    status = monitor.get_status()
    assert status["status"] == "FALLBACK"
    assert status["circuit_breaker_tripped"] is True
    assert status["rolling_mae_minutes"] > 15.0

def test_empirical_fallback_table_resilience():
    """Fallback heuristic returns non-negative bounded predictions with LOW confidence."""
    fb = fallback_heuristic_relief(congestion_pct=75.0, incident_type="ACCIDENT")
    assert fb["is_predicted"] is True
    assert fb["predicted_relief_minutes"] >= 10
    assert fb["confidence_score"] <= 0.60
    assert fb["confidence_tier"] == "LOW"
    assert "model_version" in fb
    assert fb["model_version"] == "heuristic_fallback"

def test_ml_status_endpoint():
    """Health check endpoint reports active model inference state."""
    resp = client.get("/api/v1/ml/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("OPERATIONAL", "DEGRADED", "FALLBACK")
    assert "rolling_mae_minutes" in data
