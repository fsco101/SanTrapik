"""
Unit and validation tests for Quantile Relief Envelopes (SP9-002).
Ensures P10, P50, P90 quantile bounds are non-negative, ordered P10 <= P50 <= P90,
confidence inversely scales with interval width, and relief window display is human-friendly.
"""

import pytest
from datetime import datetime, timezone
import numpy as np

from backend.app.ml.guardrails import (
    format_quantile_relief,
    clamp_relief_minutes,
    compute_confidence_score,
)
from backend.app.ml.inference import prediction_service

def test_quantile_relief_formatting_and_ordering():
    """Verify P10 <= P50 <= P90, non-negative bounds, and window formatting."""
    res = format_quantile_relief(p10=18.2, p50=28.5, p90=42.0, base_confidence=0.88)

    assert "p10_optimistic_mins" in res
    assert "p50_median_mins" in res
    assert "p90_pessimistic_mins" in res
    assert "relief_window_display" in res
    assert "confidence_score" in res

    assert res["p10_optimistic_mins"] >= 5
    assert res["p10_optimistic_mins"] <= res["p50_median_mins"]
    assert res["p50_median_mins"] <= res["p90_pessimistic_mins"]
    assert res["relief_window_display"] == "18–42 mins"

def test_confidence_inversely_correlates_with_interval_width():
    """Verify confidence score drops when prediction interval expands."""
    # Narrow window: P10=20, P90=26 (width = 6 mins)
    tight = format_quantile_relief(p10=20.0, p50=23.0, p90=26.0, base_confidence=0.90)

    # Wide window under high variance: P10=15, P90=75 (width = 60 mins)
    wide = format_quantile_relief(p10=15.0, p50=35.0, p90=75.0, base_confidence=0.90)

    assert tight["confidence_score"] > wide["confidence_score"]
    assert wide["confidence_score"] >= 0.50

def test_non_negative_guardrail_edge_cases():
    """Guardrails must guarantee non-negative lower bounds under all conditions."""
    negative_input = format_quantile_relief(p10=-15.0, p50=-5.0, p90=2.0, base_confidence=0.85)
    assert negative_input["p10_optimistic_mins"] >= 5
    assert negative_input["p50_median_mins"] >= 5
    assert negative_input["p90_pessimistic_mins"] >= negative_input["p50_median_mins"]

def test_prediction_service_outputs_quantiles():
    """Prediction service must output complete quantile envelope."""
    segments = [
        {"id": "seg_edsa_1", "current_speed": 18.0, "baseline_speed": 60.0, "distance_meters": 1200.0}
    ]
    incidents = [
        {"id": "inc_1", "type": "ACCIDENT", "severity": "HIGH", "lanes_blocked": 2, "road_width_lanes": 4}
    ]
    res = prediction_service.predict_corridor_relief(segments, incidents)

    assert "p10_optimistic_mins" in res
    assert "p50_median_mins" in res
    assert "p90_pessimistic_mins" in res
    assert "relief_window_display" in res
    assert res["p10_optimistic_mins"] <= res["p50_median_mins"] <= res["p90_pessimistic_mins"]
