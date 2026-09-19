"""
MLOps Model Drift Monitor & Fallback Circuit Breaker (SP9-004).
Monitors prediction residuals, feature distributions, and input outlier rates.
Trips automated circuit breaker to deterministic empirical MMDA lookup tables
if residual MAE > 15 minutes or outlier rate exceeds defined threshold.
"""

import time
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

def fallback_heuristic_relief(congestion_pct: float, incident_type: str = "NONE") -> Dict[str, Any]:
    """
    Deterministic fallback table based on empirical MMDA clearance averages.
    Adheres strictly to traffic-prediction-mlops skill section 5.
    """
    base_clearance = {
        "ACCIDENT": 45,
        "ACCIDENT_MAJOR": 60,
        "ACCIDENT_MINOR": 20,
        "STALLED_VEHICLE": 25,
        "STALLED_BUS": 45,
        "FLOOD": 90,
        "ROADWORK": 120,
        "NONE": 20,
    }.get(str(incident_type).upper(), 20)

    # Scale by congestion severity
    estimated = max(5, int(base_clearance * (congestion_pct / 100.0) + 10))
    p10 = max(5, estimated - 10)
    p50 = estimated
    p90 = estimated + 15

    return {
        "is_predicted": True,
        "predicted_relief_minutes": estimated,
        "expected_relief_time": (datetime.now(timezone.utc) + timedelta(minutes=estimated)).strftime("%I:%M %p").lstrip("0"),
        "relief_window_display": f"{p10}–{p90} mins",
        "p10_optimistic_mins": p10,
        "p50_median_mins": p50,
        "p90_pessimistic_mins": p90,
        "confidence_score": 0.45,
        "confidence_tier": "LOW",
        "model_version": "heuristic_fallback",
        "fallback_active": True,
    }

class DriftMonitorService:
    def __init__(self, mae_threshold: float = 15.0, outlier_threshold: float = 0.25):
        self.mae_threshold = mae_threshold
        self.outlier_threshold = outlier_threshold
        self.inferences = deque(maxlen=300)
        self.observations = deque(maxlen=100)

    def record_inference(self, features_arr: np.ndarray, predicted_minutes: float):
        """Logs model inference telemetry asynchronously."""
        now = time.time()
        is_outlier = False
        if features_arr.ndim == 1:
            features_arr = features_arr.reshape(1, -1)

        # Check for extreme outlier speed ratios (< 0.05 or > 2.0)
        if features_arr.shape[1] > 8:
            speed_ratios = features_arr[:, 8]
            if np.any(speed_ratios < 0.05) or np.any(speed_ratios > 2.0):
                is_outlier = True

        self.inferences.append({
            "timestamp": now,
            "predicted_minutes": predicted_minutes,
            "is_outlier": is_outlier,
        })

    def record_observation(self, predicted_minutes: float, observed_minutes: float):
        """Logs observed ground truth recovery comparisons."""
        residual = abs(predicted_minutes - observed_minutes)
        self.observations.append({
            "timestamp": time.time(),
            "predicted": predicted_minutes,
            "observed": observed_minutes,
            "residual": residual,
        })

    def get_status(self) -> Dict[str, Any]:
        """
        Evaluates health of ML pipeline and determines circuit breaker state.
        States:
            - OPERATIONAL: Rolling MAE <= 15m and normal inputs.
            - DEGRADED: Outlier input rate > 15%.
            - FALLBACK: Rolling MAE > 15m or outlier rate > 25%.
        """
        now = time.time()
        one_hour_ago = now - 3600.0

        # Recent inferences in the last hour
        recent_inferences = [inf for inf in self.inferences if inf["timestamp"] >= one_hour_ago]
        total_inf = len(recent_inferences)
        outlier_count = sum(1 for inf in recent_inferences if inf["is_outlier"])
        outlier_rate = (outlier_count / total_inf) if total_inf > 0 else 0.0

        # Recent observations
        recent_obs = [obs for obs in self.observations if obs["timestamp"] >= one_hour_ago]
        if recent_obs:
            rolling_mae = round(sum(o["residual"] for o in recent_obs) / len(recent_obs), 2)
        elif self.observations:
            rolling_mae = round(sum(o["residual"] for o in self.observations) / len(self.observations), 2)
        else:
            rolling_mae = 6.2  # Baseline evaluation MAE

        # State transition logic
        circuit_breaker_tripped = False
        fallback_reason = None

        if rolling_mae > self.mae_threshold:
            status = "FALLBACK"
            circuit_breaker_tripped = True
            fallback_reason = f"Model residual error spiked (Rolling MAE {rolling_mae}m > {self.mae_threshold}m)"
        elif outlier_rate > self.outlier_threshold:
            status = "FALLBACK"
            circuit_breaker_tripped = True
            fallback_reason = f"High input distribution drift (Outlier rate {int(outlier_rate * 100)}% > {int(self.outlier_threshold * 100)}%)"
        elif outlier_rate > 0.15:
            status = "DEGRADED"
        else:
            status = "OPERATIONAL"

        return {
            "status": status,
            "circuit_breaker_tripped": circuit_breaker_tripped,
            "rolling_mae_minutes": rolling_mae,
            "mae_threshold_minutes": self.mae_threshold,
            "inferences_last_hour": total_inf,
            "outlier_rate": round(outlier_rate, 3),
            "fallback_reason": fallback_reason,
            "active_model_version": "v1.4-rt-gbr" if status != "FALLBACK" else "heuristic_fallback",
        }

drift_monitor = DriftMonitorService()
