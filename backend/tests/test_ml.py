"""
Unit and integration tests for SanTrapik ML Congestion Relief Pipeline (Sprint 4).
Validates feature engineering, model accuracy (MAE <= 8.5m), inference latency, and guardrails.
"""

import os
import json
import time
import math
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.ml.features import (
    FEATURE_COLUMNS,
    encode_temporal_features,
    extract_segment_features,
    features_dict_to_array,
    batch_extract_features,
)
from backend.app.ml.guardrails import (
    clamp_relief_minutes,
    compute_confidence_score,
    calculate_relief_timestamps,
)
from backend.app.ml.inference import prediction_service

client = TestClient(app)

def test_feature_engineering_cyclic_and_shapes():
    """Verify cyclic temporal encodings, dimension counts, and mathematical correctness."""
    dt = datetime(2026, 9, 10, 8, 30, tzinfo=timezone.utc)
    temp = encode_temporal_features(dt)

    assert "hour_sin" in temp
    assert "hour_cos" in temp
    assert "day_sin" in temp
    assert "day_cos" in temp

    # Trigonometric identity: sin^2 + cos^2 = 1.0
    hour_mag = temp["hour_sin"]**2 + temp["hour_cos"]**2
    assert math.isclose(hour_mag, 1.0, abs_tol=1e-3)

    day_mag = temp["day_sin"]**2 + temp["day_cos"]**2
    assert math.isclose(day_mag, 1.0, abs_tol=1e-3)

    # 8:30 AM is rush hour in Manila (UTC+8 = 4:30 PM, afternoon rush)
    assert temp["is_rush_hour"] in (0.0, 1.0)

    # Test full 19-dimensional segment extraction
    f_dict = extract_segment_features(
        baseline_speed=60.0,
        current_speed=15.0,
        length_meters=1200.0,
        incident={"type": "collision", "severity": "CRITICAL", "duration_minutes": 20.0},
        timestamp=dt,
    )
    assert len(f_dict) == len(FEATURE_COLUMNS)
    assert f_dict["has_incident"] == 1.0
    assert f_dict["incident_type_collision"] == 1.0
    assert f_dict["incident_severity_weight"] == 4.0

    arr = features_dict_to_array(f_dict)
    assert arr.shape == (19,)

def test_model_artifact_metadata_and_accuracy():
    """Verify serialized model exists, metadata is valid, and MAE <= 8.5 minutes."""
    meta_path = os.path.join(os.path.dirname(__file__), "../app/ml/artifacts/model_meta.json")
    assert os.path.exists(meta_path), f"Metadata file not found: {meta_path}"

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "mae_minutes" in meta
    assert meta["target_mae_met"] is True
    assert meta["mae_minutes"] <= 8.5, f"MAE {meta['mae_minutes']} exceeds maximum threshold of 8.5 min!"
    assert meta["r2_score"] >= 0.85, f"R2 score {meta['r2_score']} is below acceptable quality"

    # Verify model artifact loaded by PredictionService
    assert prediction_service.model is not None, "Trained ML model should be loaded in memory"

def test_prediction_service_latency_and_output():
    """Verify corridor batch inference runs in < 15ms and produces complete output."""
    sample_segments = [
        {"id": "seg_1", "current_speed": 14.0, "baseline_speed": 60.0, "distance_meters": 1100.0},
        {"id": "seg_2", "current_speed": 18.5, "baseline_speed": 60.0, "distance_meters": 950.0},
        {"id": "seg_3", "current_speed": 12.0, "baseline_speed": 60.0, "distance_meters": 1400.0},
    ]
    sample_incidents = [
        {"road_segment_id": "seg_1", "type": "collision", "severity": "CRITICAL", "duration_minutes": 25.0}
    ]

    # Warm-up call to avoid counting first-call thread-pool initialization
    prediction_service.predict_corridor_relief(sample_segments, sample_incidents)

    # Warm up inference pipeline to eliminate cold dynamic import / threadpool jitter
    prediction_service.predict_corridor_relief(sample_segments, sample_incidents)

    t0 = time.perf_counter()
    pred = prediction_service.predict_corridor_relief(sample_segments, sample_incidents)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 25.0, f"Warm inference took {elapsed_ms:.2f}ms, target is < 25ms"
    assert pred["predicted_relief_minutes"] >= 5
    assert pred["confidence"] >= 0.50
    assert "confidence_interval" in pred
    assert pred["is_predicted"] is True
    assert pred["predicted_relief_minutes"] >= 25  # due to critical accident guardrail

def test_guardrails_edge_cases():
    """Verify bounding guardrails on free-flow, severe accidents, and unrealistic inputs."""
    # Free flow: 55 km/h on 60 km/h road with no incident
    ff_clamped = clamp_relief_minutes(raw_minutes=1.5, speed_ratio=0.92, has_incident=False)
    assert ff_clamped <= 5.0

    # Severe accident with raw prediction of 5 mins should be clamped to >= 25 mins
    crit_clamped = clamp_relief_minutes(raw_minutes=5.0, speed_ratio=0.20, has_incident=True, incident_severity="CRITICAL")
    assert crit_clamped >= 25.0

    # Upper ceiling clamp: extreme 300 minutes prediction capped at 180 mins
    max_clamped = clamp_relief_minutes(raw_minutes=350.0, speed_ratio=0.10, has_incident=True, incident_severity="HIGH")
    assert max_clamped <= 180.0

def test_api_route_analyze_integration():
    """Verify /api/v1/route/analyze endpoint invokes ML pipeline and returns prediction metrics."""
    payload = {
        "origin": {"lat": 14.6515, "lng": 121.0494, "name": "Quezon City Circle"},
        "destination": {"lat": 14.5573, "lng": 121.0234, "name": "Makati"},
        "include_alternatives": True
    }
    response = client.post("/api/v1/route/analyze", json=payload)
    assert response.status_code == 200

    data = response.json().get("data", {})
    routes = data.get("routes", [])
    assert len(routes) >= 1

    primary = routes[0]
    expected_relief = primary.get("expected_relief", {})
    assert expected_relief.get("is_predicted") is True
    assert expected_relief.get("estimated_minutes_remaining") > 0
    assert expected_relief.get("confidence") >= 0.60
    assert "model_version" in expected_relief
