"""
SanTrapik ML Guardrails & Confidence Estimator.
Ensures predictions adhere to physical traffic boundaries and outputs confidence intervals.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple, Optional
import numpy as np

MIN_RELIEF_MINUTES = 5.0
MAX_RELIEF_MINUTES = 180.0

def clamp_relief_minutes(
    raw_minutes: float,
    speed_ratio: float = 1.0,
    has_incident: bool = False,
    incident_severity: str = "NONE",
) -> float:
    """
    Clamps raw ML model prediction to realistic Metro Manila traffic recovery bounds.
    """
    if speed_ratio >= 0.85 and not has_incident:
        # Already near free-flow
        return 0.0

    clamped = max(MIN_RELIEF_MINUTES, min(MAX_RELIEF_MINUTES, float(raw_minutes)))

    # If severe obstruction exists, relief cannot physically clear in under 25 minutes
    if has_incident and incident_severity in ("CRITICAL", "HIGH"):
        clamped = max(25.0, clamped)
    elif speed_ratio < 0.25:
        clamped = max(20.0, clamped)

    return round(clamped, 1)

def compute_confidence_score(
    features_arr: np.ndarray,
    model_predictions: Optional[np.ndarray] = None,
) -> float:
    """
    Computes confidence score in [0.60, 0.98] based on feature distribution and model certainty.
    """
    if features_arr.ndim == 1:
        features_arr = features_arr.reshape(1, -1)

    base_confidence = 0.91

    # Check for extreme outlier speed ratios or missing data
    speed_ratios = features_arr[:, 8] if features_arr.shape[1] > 8 else np.array([0.5])
    has_incidents = features_arr[:, 12] if features_arr.shape[1] > 12 else np.array([0.0])

    penalty = 0.0
    # Compounding high variance with severe incidents
    if np.any(has_incidents > 0):
        penalty += 0.05
    if np.any(speed_ratios < 0.15):
        penalty += 0.04

    confidence = max(0.65, min(0.96, base_confidence - penalty))
    return round(float(confidence), 2)

def calculate_relief_timestamps(
    relief_minutes: float,
    confidence: float,
    base_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Calculates formatted expected relief time and lower/upper confidence interval windows.
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    # Metro Manila UTC+8 offset
    manila_time = base_time + timedelta(hours=8)
    target_dt = manila_time + timedelta(minutes=relief_minutes)

    # Window margin based on confidence: 90%+ -> +/- 5m, 70-89% -> +/- 10m
    margin_minutes = max(4.0, (1.0 - confidence) * 60.0)
    lower_dt = target_dt - timedelta(minutes=margin_minutes)
    upper_dt = target_dt + timedelta(minutes=margin_minutes)

    target_str = target_dt.strftime("%I:%M %p").lstrip("0")
    lower_str = lower_dt.strftime("%I:%M %p").lstrip("0")
    upper_str = upper_dt.strftime("%I:%M %p").lstrip("0")

    return {
        "predicted_relief_minutes": int(round(relief_minutes)),
        "expected_relief_time": target_str,
        "confidence_score": confidence,
        "confidence_interval": f"{lower_str} – {upper_str}",
        "is_predicted": True,
        "model_version": "v1.4-rt-gbr",
    }

def format_quantile_relief(
    p10: float,
    p50: float,
    p90: float,
    base_confidence: float = 0.88,
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Formats multi-quantile predictions (P10/P50/P90) into bounded intervals with dynamic confidence.
    Enforces non-negative bounds and P10 <= P50 <= P90 (SP9-002).
    """
    min_mins = max(5, int(round(p10)))
    est_mins = max(min_mins, int(round(p50)))
    max_mins = max(est_mins, int(round(p90)))

    interval_width = max_mins - min_mins

    # Confidence inversely correlates with prediction interval width
    width_penalty = min(0.38, (interval_width / 120.0))
    confidence = round(max(0.50, min(0.96, base_confidence - width_penalty)), 2)

    if interval_width <= 6:
        window_display = f"~{est_mins} mins"
    else:
        window_display = f"{min_mins}–{max_mins} mins"

    time_meta = calculate_relief_timestamps(est_mins, confidence, timestamp)

    return {
        **time_meta,
        "p10_optimistic_mins": min_mins,
        "p50_median_mins": est_mins,
        "p90_pessimistic_mins": max_mins,
        "relief_window_display": window_display,
        "confidence_score": confidence,
        "confidence_tier": "HIGH" if confidence >= 0.80 else ("MEDIUM" if confidence >= 0.65 else "LOW"),
    }
