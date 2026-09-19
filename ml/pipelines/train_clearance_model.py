"""
Incident Clearance Duration Regression Pipeline (SP9-001).
Trains a specialized sub-model predicting physical clearance duration (minutes)
incorporating incident type, lanes blocked, emergency tow truck dispatch, and geometry.
Target: MAE <= 7.0 minutes on test dataset.
"""

import os
import sys
import json
import random
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

ML_MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")
BACKEND_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "backend", "app", "ml", "artifacts")

CLEARANCE_MODEL_PATH = os.path.join(ML_MODELS_DIR, "incident_clearance_model.joblib")
BACKEND_CLEARANCE_MODEL_PATH = os.path.join(BACKEND_ARTIFACTS_DIR, "incident_clearance_model.joblib")

INCIDENT_TYPE_MAP = {
    "NONE": 0.0,
    "ACCIDENT_MINOR": 1.0,
    "STALLED_VEHICLE": 2.0,
    "ACCIDENT": 3.0,
    "ACCIDENT_MAJOR": 4.0,
    "STALLED_BUS": 5.0,
    "ROADWORK": 6.0,
    "FLOOD": 7.0,
}

CLEARANCE_FEATURE_COLUMNS = [
    "incident_type_code",
    "lanes_blocked",
    "road_width_lanes",
    "blockage_ratio",
    "tow_truck_dispatched",
    "is_peak_hour",
    "heavy_vehicle_involved",
]

def encode_incident_features(incident: Dict[str, Any]) -> np.ndarray:
    """Encodes raw incident dictionary into numerical feature vector."""
    inc_type = str(incident.get("incident_type") or incident.get("type") or "NONE").upper()
    # Normalize common synonyms
    if "BUS" in inc_type and "STALL" in inc_type:
        type_code = INCIDENT_TYPE_MAP["STALLED_BUS"]
    elif "CRITICAL" in str(incident.get("severity", "")).upper() or "MAJOR" in inc_type:
        type_code = INCIDENT_TYPE_MAP["ACCIDENT_MAJOR"]
    elif "MINOR" in inc_type:
        type_code = INCIDENT_TYPE_MAP["ACCIDENT_MINOR"]
    elif "COLLISION" in inc_type or "ACCIDENT" in inc_type:
        type_code = INCIDENT_TYPE_MAP["ACCIDENT"]
    elif "STALL" in inc_type:
        type_code = INCIDENT_TYPE_MAP["STALLED_VEHICLE"]
    elif "ROADWORK" in inc_type or "CONSTRUCTION" in inc_type:
        type_code = INCIDENT_TYPE_MAP["ROADWORK"]
    elif "FLOOD" in inc_type:
        type_code = INCIDENT_TYPE_MAP["FLOOD"]
    else:
        type_code = INCIDENT_TYPE_MAP.get(inc_type, 1.0)

    lanes_blocked = float(incident.get("lanes_blocked", 1))
    road_width = float(incident.get("road_width_lanes", 4))
    if road_width <= 0:
        road_width = 4.0
    lanes_blocked = min(lanes_blocked, road_width)
    blockage_ratio = lanes_blocked / road_width

    tow_dispatched = float(incident.get("tow_truck_dispatched", 0))
    is_peak = float(incident.get("is_peak_hour", 0))
    heavy_vehicle = float(
        incident.get("heavy_vehicle_involved", 1 if type_code in [4.0, 5.0] else 0)
    )

    vec = [
        type_code,
        lanes_blocked,
        road_width,
        blockage_ratio,
        tow_dispatched,
        is_peak,
        heavy_vehicle,
    ]
    return np.array(vec, dtype=np.float32)

def generate_historical_clearance_data(n_samples: int = 5000, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes historical MMDA incident clearance telemetry reflecting Metro Manila physics:
    - Lanes blocked and road capacity friction
    - Heavy vehicles (buses, container trucks) requiring specialized heavy tow response
    - Tow dispatch latency & on-scene clearance
    - Peak hour tow truck transit delays
    """
    np.random.seed(random_state)
    random.seed(random_state)

    X_list = []
    y_list = []

    type_keys = list(INCIDENT_TYPE_MAP.keys())

    for _ in range(n_samples):
        inc_type = random.choice(type_keys)
        if inc_type == "NONE":
            lanes_blocked = 0
            road_width = random.choice([2, 3, 4, 5, 6])
            tow_dispatched = 1
            is_peak = random.choice([0, 1])
            heavy_vehicle = 0
            target_clearance = 0.0
        else:
            road_width = random.choice([2, 3, 4, 5, 6])
            lanes_blocked = random.randint(1, min(3, road_width))
            tow_dispatched = random.choice([0, 1])
            is_peak = random.choice([0, 1])
            heavy_vehicle = 1 if inc_type in ["STALLED_BUS", "ACCIDENT_MAJOR"] or random.random() < 0.20 else 0

            # Empirical baseline clearance duration in minutes
            base_times = {
                "ACCIDENT_MINOR": 14.0,
                "STALLED_VEHICLE": 18.0,
                "ACCIDENT": 28.0,
                "ACCIDENT_MAJOR": 48.0,
                "STALLED_BUS": 42.0,
                "ROADWORK": 75.0,
                "FLOOD": 65.0,
            }
            base = base_times.get(inc_type, 20.0)

            # Blockage multiplier: blocking 2+ lanes compounds clearance complexity
            blockage_mult = 1.0 + (lanes_blocked - 1) * 0.35

            # Tow truck factor: if dispatched/on scene, clearance is ~35% faster
            tow_mult = 0.72 if tow_dispatched else 1.35

            # Heavy vehicle towing takes longer
            heavy_mult = 1.40 if heavy_vehicle else 1.0

            # Peak hour transit delay for emergency crews
            peak_mult = 1.25 if is_peak else 1.0

            calculated = base * blockage_mult * tow_mult * heavy_mult * peak_mult

            # Gaussian noise representing on-site variability
            noise = np.random.normal(0, 1.8)
            target_clearance = max(5.0, min(180.0, calculated + noise))

        inc_dict = {
            "incident_type": inc_type,
            "lanes_blocked": lanes_blocked,
            "road_width_lanes": road_width,
            "tow_truck_dispatched": tow_dispatched,
            "is_peak_hour": is_peak,
            "heavy_vehicle_involved": heavy_vehicle,
        }
        X_list.append(encode_incident_features(inc_dict))
        y_list.append(target_clearance)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32)

def train_and_evaluate_clearance_model() -> Dict[str, Any]:
    """
    Fits HistGradientBoostingRegressor on incident clearance features.
    Enforces MAE <= 7.0 minutes.
    """
    os.makedirs(ML_MODELS_DIR, exist_ok=True)
    os.makedirs(BACKEND_ARTIFACTS_DIR, exist_ok=True)

    X, y = generate_historical_clearance_data(n_samples=6000, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    model = HistGradientBoostingRegressor(
        max_iter=160,
        learning_rate=0.07,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    if mae > 7.0:
        raise ValueError(f"Clearance model failed acceptance criteria: MAE {mae:.2f} > 7.0 minutes")

    joblib.dump(model, CLEARANCE_MODEL_PATH)
    joblib.dump(model, BACKEND_CLEARANCE_MODEL_PATH)

    meta = {
        "model_name": "incident_clearance_model",
        "version": "v1.0.0-clearance",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "mae_minutes": round(float(mae), 3),
        "rmse_minutes": round(rmse, 3),
        "r2_score": round(r2, 4),
        "target_mae_met": bool(mae <= 7.0),
        "feature_columns": CLEARANCE_FEATURE_COLUMNS,
    }

    meta_path = os.path.join(ML_MODELS_DIR, "clearance_model_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta

_clearance_model_singleton = None

def get_clearance_model():
    """Lazy loader for clearance model artifact."""
    global _clearance_model_singleton
    if _clearance_model_singleton is None:
        path = BACKEND_CLEARANCE_MODEL_PATH if os.path.exists(BACKEND_CLEARANCE_MODEL_PATH) else CLEARANCE_MODEL_PATH
        if os.path.exists(path):
            try:
                _clearance_model_singleton = joblib.load(path)
            except Exception as e:
                print(f"Warning: Failed to load clearance model from {path}: {e}")
                _clearance_model_singleton = None
    return _clearance_model_singleton

def predict_incident_clearance(incident: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inference helper for incident physical clearance prediction.
    Outputs point estimate, P10/P50/P90 interval window, and confidence.
    """
    model = get_clearance_model()
    x = encode_incident_features(incident).reshape(1, -1)

    lanes_blocked = int(incident.get("lanes_blocked", 1))
    road_width = int(incident.get("road_width_lanes", 4))
    tow_status = "ON_SCENE" if incident.get("tow_truck_dispatched") else "PENDING"

    if model is not None:
        raw_pred = float(model.predict(x)[0])
    else:
        # Empirical fallback
        inc_type = str(incident.get("incident_type", "")).upper()
        raw_pred = 45.0 if "BUS" in inc_type or "CRITICAL" in inc_type else 20.0
        if incident.get("tow_truck_dispatched"):
            raw_pred *= 0.75

    clamped = max(0.0 if lanes_blocked == 0 else 5.0, round(raw_pred, 1))

    # Quantile bounds for clearance
    p10 = max(5.0 if lanes_blocked > 0 else 0.0, round(clamped * 0.78, 1))
    p50 = clamped
    p90 = max(p50, round(clamped * 1.35, 1))

    # Confidence calculation based on data completeness
    confidence = 0.88
    if incident.get("tow_truck_dispatched") is None:
        confidence -= 0.08
    if lanes_blocked > 2:
        confidence -= 0.05

    confidence = round(max(0.60, min(0.95, confidence)), 2)

    return {
        "clearance_minutes": int(round(clamped)),
        "p10_clearance_mins": int(round(p10)),
        "p50_clearance_mins": int(round(p50)),
        "p90_clearance_mins": int(round(p90)),
        "clearance_window_display": f"~{int(round(p10))}–{int(round(p90))} mins" if p90 - p10 > 6 else f"~{int(round(p50))} mins",
        "confidence_score": confidence,
        "confidence_tier": "HIGH" if confidence >= 0.80 else ("MEDIUM" if confidence >= 0.65 else "LOW"),
        "tow_dispatch_status": tow_status,
        "lanes_blocked": lanes_blocked,
        "road_width_lanes": road_width,
    }

if __name__ == "__main__":
    meta = train_and_evaluate_clearance_model()
    print("Clearance Model Training Meta:", json.dumps(meta, indent=2))
