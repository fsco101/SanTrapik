---
name: traffic-prediction-mlops
description: Use when building, evaluating, serving, or debugging machine learning models and heuristics for congestion relief forecasting, feature extraction, and traffic bottleneck diagnostics
---

# Traffic Prediction & Congestion Relief MLOps

## Overview
Standard navigation apps tell drivers where traffic is right now; SanTrapik's core differentiator is **predictive traffic intelligence**: forecasting **when** congestion will ease (`predicted_relief_minutes`) and diagnosing **what** is causing the bottleneck.

This skill provides the machine learning pipeline standards, spatiotemporal feature engineering patterns for Metro Manila, confidence interval bounding (P10/P50/P90), and model serving guardrails.

---

## 1. Problem Formulation & Metrics

### The Target Variable: Time-to-Relief ($\Delta t_{\text{relief}}$)
The prediction target is defined as the elapsed time in minutes from the current observation timestamp ($t_0$) until the corridor's average velocity recovers to $\ge 80\%$ of its designated baseline free-flow speed ($v_{\text{baseline}}$):
$$\Delta t_{\text{relief}} = \min \{ \Delta t > 0 \mid v(t_0 + \Delta t) \ge 0.80 \times v_{\text{baseline}} \}$$

### Evaluation Guardrails
- **Primary Metric**: Mean Absolute Error (MAE) $\le 8.5\text{ minutes}$ across peak chokepoint test sets.
- **Secondary Metric**: Root Mean Squared Error (RMSE) $\le 12.0\text{ minutes}$ (penalizing catastrophic under-predictions).
- **Asymmetric Penalty Rule**: Under-predicting relief time (telling a driver traffic will clear in 10 mins when it takes 50 mins) causes high commuter frustration. Over-predicting is preferred over false optimism.

---

## 2. Metro Manila Spatiotemporal Feature Engineering

```python
# ml/pipelines/feature_engineering.py
import numpy as np
import pandas as pd
from datetime import datetime

def extract_spatiotemporal_features(row: dict) -> dict:
    """Extracts cyclic, corridor, and incident features for relief regression."""
    timestamp = row["timestamp"]
    hour = timestamp.hour + timestamp.minute / 60.0
    day_of_week = timestamp.weekday()

    # 1. Cyclic time-of-day encoding (24-hour periodicity)
    sin_hour = np.sin(2 * np.pi * hour / 24.0)
    cos_hour = np.cos(2 * np.pi * hour / 24.0)

    # 2. Manila specific peak hour indicators
    is_morning_rush = 1 if (7.0 <= hour <= 10.0 and day_of_week < 5) else 0
    is_evening_rush = 1 if (17.0 <= hour <= 21.0 and day_of_week < 5) else 0
    is_payday_friday = 1 if (day_of_week == 4 and timestamp.day in [14, 15, 16, 29, 30, 31]) else 0

    # 3. Current velocity friction ratio
    speed = max(1.0, row["current_speed_kmh"])
    baseline = max(20.0, row["baseline_speed_kmh"])
    velocity_ratio = speed / baseline  # e.g., 0.20 = severe congestion

    # 4. Bottleneck & Incident severity weights
    incident_active = 1 if row.get("incident_id") else 0
    incident_type = row.get("incident_type", "NONE")
    # Multiplier reflecting clearance physics (stalled heavy bus blocks 2+ lanes on EDSA)
    severity_weights = {
        "NONE": 0.0,
        "STALLED_VEHICLE": 1.5,
        "ACCIDENT": 2.2,
        "ROADWORK": 3.0,
        "FLOOD": 4.5  # Flood clearance depends on tidal / drainage pump cycles
    }
    incident_friction = severity_weights.get(incident_type, 1.0) * incident_active

    return {
        "sin_hour": sin_hour,
        "cos_hour": cos_hour,
        "day_of_week": day_of_week,
        "is_morning_rush": is_morning_rush,
        "is_evening_rush": is_evening_rush,
        "is_payday_friday": is_payday_friday,
        "velocity_ratio": velocity_ratio,
        "incident_active": incident_active,
        "incident_friction": incident_friction,
        "current_congestion_pct": round((1.0 - velocity_ratio) * 100.0, 1)
    }
```

---

## 3. Probabilistic Bounding (Quantile Bounds P10 / P50 / P90)

Point-in-time predictions (e.g., "Clears at exactly 6:42 PM") give a false sense of certainty in chaotic urban environments. Model inference must output **bounded prediction windows**:

```python
# backend/app/ml/inference.py
from typing import Dict, Any

def format_relief_prediction(p10: float, p50: float, p90: float, confidence: float) -> Dict[str, Any]:
    """
    Formats model quantiles into human-transparent telemetry response.
    """
    # Clamp non-negative
    min_mins = max(5, int(round(p10)))
    est_mins = max(min_mins, int(round(p50)))
    max_mins = max(est_mins, int(round(p90)))

    # Window description for UI
    if max_mins - min_mins <= 10:
        window_display = f"~{est_mins} mins"
    else:
        window_display = f"{min_mins}–{max_mins} mins"

    return {
        "is_predicted": True,
        "predicted_relief_minutes": est_mins,
        "relief_window_display": window_display,
        "p10_optimistic_mins": min_mins,
        "p50_median_mins": est_mins,
        "p90_pessimistic_mins": max_mins,
        "confidence_score": round(confidence, 2),
        "confidence_tier": "HIGH" if confidence >= 0.80 else ("MEDIUM" if confidence >= 0.55 else "LOW"),
        "model_version": "v1.2.0-rf-manila"
    }
```

---

## 4. Transparent Separation: Observed vs. Predicted

Strict adherence to **Operating Principle 3** from `AGENT.md`:
1. **Never conflate observed speed with predicted relief**: Ground-truth speed is an observed measurement; relief time is a statistical forecast.
2. **Distinct Semantic Colors**:
   - Observed conditions use the traffic signal spectrum: Green (`#10B981`), Amber (`#F59E0B`), Orange (`#F97316`), Red (`#EF4444`).
   - Predicted relief metrics strictly use the AI electric glow spectrum: Indigo (`#6366F1`) and Cyan (`#06B6D4`).
3. **Always display model confidence**: Never omit the confidence meter (`confidence_score`) from the API response or UI card.

---

## 5. Graceful Degradation & Fallback Heuristics

If the ML artifact is unavailable, corrupted, or receives out-of-distribution inputs (e.g. typhoon Signal No. 3 conditions where all models lose calibration):

```python
def fallback_heuristic_relief(congestion_pct: float, incident_type: str) -> dict:
    """Deterministic fallback table based on empirical MMDA clearance averages."""
    base_clearance = {
        "ACCIDENT": 45,
        "STALLED_VEHICLE": 25,
        "FLOOD": 90,
        "ROADWORK": 120,
        "NONE": 20
    }.get(incident_type, 20)

    # Scale by congestion severity
    estimated = int(base_clearance * (congestion_pct / 100.0) + 10)
    return {
        "is_predicted": True,
        "predicted_relief_minutes": estimated,
        "relief_window_display": f"{max(5, estimated - 10)}–{estimated + 15} mins",
        "confidence_score": 0.45,
        "confidence_tier": "LOW",
        "model_version": "heuristic_fallback"
    }
```

---

## 6. MLOps Quality Checklist

1. [ ] **Non-Negative Output**: Ensure `predicted_relief_minutes >= 0` under all input ranges.
2. [ ] **Inference Latency**: Batch inference on all route segments must execute in $\le 15\text{ ms}$.
3. [ ] **Serialization Portability**: Models must serialize with `joblib` or ONNX and load cleanly in headless Python environments without GPU requirements.
4. [ ] **Zero Fabricated Accuracy**: If confidence is low ($< 0.50$), widen the prediction window (`30–60 mins`) rather than displaying a precise point estimate.
