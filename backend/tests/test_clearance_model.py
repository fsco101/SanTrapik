"""
Unit and validation tests for SanTrapik Incident Clearance Duration Pipeline (SP9-001).
Ensures clearance sub-model achieves MAE <= 7.0 minutes on historical MMDA incident data
and properly predicts physical clearance physics (lanes blocked, tow dispatch, geometry).
"""

import os
import pytest
import numpy as np

from ml.pipelines.train_clearance_model import (
    train_and_evaluate_clearance_model,
    predict_incident_clearance,
    CLEARANCE_MODEL_PATH,
    CLEARANCE_FEATURE_COLUMNS,
)

def test_clearance_model_training_and_mae():
    """Verify clearance model trains and meets acceptance criteria MAE <= 7.0 minutes."""
    meta = train_and_evaluate_clearance_model()
    assert meta["target_mae_met"] is True
    assert meta["mae_minutes"] <= 7.0
    assert os.path.exists(CLEARANCE_MODEL_PATH)

def test_clearance_prediction_physics():
    """Verify clearance duration scales realistically with blockage physics and tow status."""
    # 1. Minor fender bender: 1 lane blocked out of 4, tow dispatched
    minor_incident = {
        "incident_type": "ACCIDENT_MINOR",
        "lanes_blocked": 1,
        "road_width_lanes": 4,
        "tow_truck_dispatched": 1,
        "is_peak_hour": 0,
        "heavy_vehicle_involved": 0,
    }
    pred_minor = predict_incident_clearance(minor_incident)
    assert 5.0 <= pred_minor["clearance_minutes"] <= 25.0
    assert pred_minor["confidence_score"] >= 0.70

    # 2. Severe stalled bus: 2 lanes blocked out of 3, tow truck NOT dispatched
    severe_incident = {
        "incident_type": "STALLED_BUS",
        "lanes_blocked": 2,
        "road_width_lanes": 3,
        "tow_truck_dispatched": 0,
        "is_peak_hour": 1,
        "heavy_vehicle_involved": 1,
    }
    pred_severe = predict_incident_clearance(severe_incident)
    assert pred_severe["clearance_minutes"] > pred_minor["clearance_minutes"]
    assert pred_severe["clearance_minutes"] >= 30.0

def test_clearance_prediction_guardrails():
    """Verify clearance predictions are non-negative and bounded."""
    edge_incident = {
        "incident_type": "NONE",
        "lanes_blocked": 0,
        "road_width_lanes": 4,
        "tow_truck_dispatched": 1,
        "is_peak_hour": 0,
        "heavy_vehicle_involved": 0,
    }
    pred = predict_incident_clearance(edge_incident)
    assert pred["clearance_minutes"] >= 0.0
