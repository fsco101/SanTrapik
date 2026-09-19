"""
PredictionService for SanTrapik ML Congestion Relief Forecasting.
Loads trained model artifact into memory and performs sub-15ms corridor inference.
"""

import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import joblib

from backend.app.ml.features import (
    FEATURE_COLUMNS,
    batch_extract_features,
    extract_segment_features,
    features_dict_to_array,
)
from backend.app.ml.guardrails import (
    clamp_relief_minutes,
    compute_confidence_score,
    calculate_relief_timestamps,
    format_quantile_relief,
)
from ml.pipelines.train_clearance_model import predict_incident_clearance
from backend.app.services.drift_monitor import drift_monitor, fallback_heuristic_relief

MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "relief_model.joblib")
CLEARANCE_MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "incident_clearance_model.joblib")

class PredictionService:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_PATH
        self.clearance_model_path = CLEARANCE_MODEL_PATH
        self.model = None
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Failed to load ML model from {self.model_path}: {e}")
                self.model = None
        else:
            print(f"Warning: Model artifact not found at {self.model_path}. Will use fallback heuristic.")

    def predict_incident_clearance(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Predicts physical incident clearance duration, bounds, and tow truck status (SP9-001)."""
        return predict_incident_clearance(incident)

    def predict_corridor_relief(
        self,
        segments: List[Dict[str, Any]],
        incidents: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Performs high-throughput (< 15ms) inference predicting relief time and quantile bounds
        (P10, P50, P90) for a route corridor, combining incident clearance physics (SP9-001, SP9-002).
        Checks MLOps drift monitor circuit breaker state (SP9-004).
        """
        start_t = time.perf_counter()

        # SP9-004: Check Circuit Breaker status
        drift_state = drift_monitor.get_status()
        if drift_state.get("status") == "FALLBACK":
            avg_cong = float(np.mean([s.get("congestion_percentage", 45.0) for s in segments])) if segments else 45.0
            primary_inc_type = str(incidents[0].get("type", "NONE")) if incidents else "NONE"
            fb_res = fallback_heuristic_relief(avg_cong, primary_inc_type)
            fb_res["confidence"] = fb_res["confidence_score"]
            fb_res["inference_latency_ms"] = round((time.perf_counter() - start_t) * 1000.0, 2)
            return fb_res

        if not segments:
            res = format_quantile_relief(5.0, 5.0, 10.0, 0.90, timestamp)
            res["confidence"] = res["confidence_score"]
            res["inference_latency_ms"] = 0.5
            return res

        # Batch feature extraction
        X = batch_extract_features(segments, incidents, timestamp)

        # Calculate summary metrics for guardrails
        speeds = [s.get("current_speed", 30.0) for s in segments]
        baselines = [s.get("baseline_speed", 50.0) for s in segments]
        min_speed_ratio = min((s / b) for s, b in zip(speeds, baselines)) if speeds else 1.0

        has_any_incident = bool(incidents and len(incidents) > 0)
        max_severity = "NONE"
        max_incident_clearance = 0.0

        if has_any_incident and incidents:
            severities = [str(inc.get("severity", "MEDIUM")).upper() for inc in incidents]
            if "CRITICAL" in severities:
                max_severity = "CRITICAL"
            elif "HIGH" in severities:
                max_severity = "HIGH"
            elif "MEDIUM" in severities:
                max_severity = "MEDIUM"
            else:
                max_severity = "LOW"

            # SP9-001: Physical clearance duration of active incidents
            clearance_durations = [
                float(self.predict_incident_clearance(inc)["clearance_minutes"])
                for inc in incidents
            ]
            if clearance_durations:
                max_incident_clearance = max(clearance_durations)

        # Model Inference
        if self.model is not None and len(X) > 0:
            segment_relief_predictions = self.model.predict(X)
            raw_corridor_relief = float(np.max(segment_relief_predictions))
        else:
            # Physics-based fallback if model not loaded
            deficit = max(0.0, 50.0 - np.mean(speeds))
            raw_corridor_relief = deficit * 0.8 + (30.0 if max_severity == "CRITICAL" else 10.0)

        # SP9-001: Corridor cannot recover before the incident physically clears + queue dissipates
        if max_incident_clearance > 0:
            raw_corridor_relief = max(raw_corridor_relief, max_incident_clearance + 8.0)

        # Guardrails and clamping
        guarded_relief = clamp_relief_minutes(
            raw_minutes=raw_corridor_relief,
            speed_ratio=min_speed_ratio,
            has_incident=has_any_incident,
            incident_severity=max_severity,
        )

        # Confidence Estimation
        confidence = compute_confidence_score(X)

        # SP9-002: Probabilistic Quantile Envelopes (P10 / P50 / P90)
        p50 = guarded_relief
        p10 = max(5.0, guarded_relief * 0.78)
        p90 = max(p50, guarded_relief * 1.30 + (12.0 if has_any_incident else 5.0))

        result = format_quantile_relief(
            p10=p10,
            p50=p50,
            p90=p90,
            base_confidence=confidence,
            timestamp=timestamp,
        )
        result["confidence"] = result["confidence_score"]
        latency_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        result["inference_latency_ms"] = latency_ms

        # SP9-004: Record inference telemetry asynchronously in drift monitor
        try:
            drift_monitor.record_inference(X, result["predicted_relief_minutes"])
        except Exception:
            pass

        return result

# Singleton instance
prediction_service = PredictionService()
