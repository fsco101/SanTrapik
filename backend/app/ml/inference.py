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
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "artifacts", "relief_model.joblib")

class PredictionService:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or MODEL_PATH
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

    def predict_corridor_relief(
        self,
        segments: List[Dict[str, Any]],
        incidents: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Performs high-throughput (< 15ms) inference predicting relief time for a route corridor.
        """
        start_t = time.perf_counter()

        if not segments:
            return calculate_relief_timestamps(5.0, 0.90, timestamp)

        # Batch feature extraction
        X = batch_extract_features(segments, incidents, timestamp)

        # Calculate summary metrics for guardrails
        speeds = [s.get("current_speed", 30.0) for s in segments]
        baselines = [s.get("baseline_speed", 50.0) for s in segments]
        min_speed_ratio = min((s / b) for s, b in zip(speeds, baselines)) if speeds else 1.0

        has_any_incident = bool(incidents and len(incidents) > 0)
        max_severity = "NONE"
        if has_any_incident:
            severities = [str(inc.get("severity", "MEDIUM")).upper() for inc in incidents]
            if "CRITICAL" in severities:
                max_severity = "CRITICAL"
            elif "HIGH" in severities:
                max_severity = "HIGH"
            elif "MEDIUM" in severities:
                max_severity = "MEDIUM"
            else:
                max_severity = "LOW"

        # Model Inference
        if self.model is not None and len(X) > 0:
            segment_relief_predictions = self.model.predict(X)
            # The bottleneck segment dictates the recovery time of the corridor
            raw_corridor_relief = float(np.max(segment_relief_predictions))
        else:
            # Physics-based fallback if model not loaded
            deficit = max(0.0, 50.0 - np.mean(speeds))
            raw_corridor_relief = deficit * 0.8 + (30.0 if max_severity == "CRITICAL" else 10.0)

        # Guardrails and clamping
        guarded_relief = clamp_relief_minutes(
            raw_minutes=raw_corridor_relief,
            speed_ratio=min_speed_ratio,
            has_incident=has_any_incident,
            incident_severity=max_severity,
        )

        # Confidence Estimation
        confidence = compute_confidence_score(X)

        # Formatted Timestamps & Interval Window
        result = calculate_relief_timestamps(guarded_relief, confidence, timestamp)
        result["confidence"] = confidence
        latency_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        result["inference_latency_ms"] = latency_ms

        return result

# Singleton instance
prediction_service = PredictionService()
