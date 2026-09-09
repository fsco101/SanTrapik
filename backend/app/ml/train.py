"""
Model training and evaluation pipeline for SanTrapik Congestion Relief Prediction.
Trains Gradient Boosting Regressor targeting MAE <= 8.5 minutes and serializes model artifacts.
"""

import os
import sys
import json
import random
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

# Ensure repository root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.ml.features import (
    FEATURE_COLUMNS,
    extract_segment_features,
    features_dict_to_array,
)

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
ML_MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")

def generate_training_dataset(n_samples: int = 4000, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes realistic Metro Manila training samples reflecting traffic dynamics,
    bottlenecks (Ortigas, Guadalupe, Bagong Ilog), rush hours, and road incidents.
    """
    np.random.seed(random_state)
    random.seed(random_state)

    X_list = []
    y_list = []

    corridor_baselines = [40.0, 50.0, 60.0, 80.0]
    incident_types = [
        None,
        {"type": "collision", "severity": "CRITICAL", "duration_minutes": 45.0},
        {"type": "collision", "severity": "HIGH", "duration_minutes": 25.0},
        {"type": "roadwork", "severity": "MEDIUM", "duration_minutes": 120.0},
        {"type": "flood", "severity": "HIGH", "duration_minutes": 60.0},
        {"type": "stall", "severity": "MEDIUM", "duration_minutes": 15.0},
    ]

    for _ in range(n_samples):
        hour = np.random.uniform(0, 24)
        is_rush = 1 if (7.0 <= hour <= 10.0 or 17.0 <= hour <= 21.0) else 0
        baseline = random.choice(corridor_baselines)

        # Speed distribution depends on rush hour and incidents
        incident = random.choice(incident_types)
        if incident and incident["severity"] == "CRITICAL":
            current_speed = np.random.uniform(4.0, 12.0)
        elif is_rush:
            current_speed = np.random.uniform(8.0, baseline * 0.55)
        else:
            current_speed = np.random.uniform(baseline * 0.40, baseline * 0.95)

        length_m = np.random.uniform(400, 2500)

        # Realistic physics-based ground truth relief time (minutes)
        speed_deficit = max(0.0, baseline - current_speed)
        speed_ratio = current_speed / baseline

        base_relief = speed_deficit * 0.75

        # Rush hour backlog multiplier
        if is_rush:
            base_relief *= 1.45

        # Incident clearance factor
        if incident:
            sev_multiplier = {
                "CRITICAL": 35.0,
                "HIGH": 20.0,
                "MEDIUM": 12.0,
                "LOW": 6.0,
            }.get(incident["severity"], 10.0)
            base_relief += sev_multiplier

        # Add Gaussian noise
        noise = np.random.normal(0, 2.5)
        target_relief = max(5.0, min(180.0, base_relief + noise))

        # Free-flow traffic clears quickly
        if speed_ratio >= 0.85 and not incident:
            target_relief = np.random.uniform(0.0, 4.0)

        f_dict = extract_segment_features(
            baseline_speed=baseline,
            current_speed=current_speed,
            length_meters=length_m,
            incident=incident,
            timestamp=datetime(2026, 9, 10, int(hour) % 24, int((hour % 1) * 60)),
        )

        X_list.append(features_dict_to_array(f_dict))
        y_list.append(target_relief)

    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32)

def train_and_evaluate() -> Dict[str, Any]:
    """Trains Gradient Boosting Regressor and validates MAE <= 8.5 minutes."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    os.makedirs(ML_MODELS_DIR, exist_ok=True)

    print("Synthesizing training and validation datasets...")
    X, y = generate_training_dataset(n_samples=5000, random_state=42)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    print(f"Training dataset size: {X_train.shape[0]}, Test dataset size: {X_test.shape[0]}")
    print("Fitting HistGradientBoostingRegressor...")

    model = HistGradientBoostingRegressor(
        max_iter=150,
        learning_rate=0.08,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation Results ---")
    print(f"Mean Absolute Error (MAE): {mae:.2f} minutes (Target: <= 8.5 min)")
    print(f"Root Mean Squared Error (RMSE): {rmse:.2f} minutes")
    print(f"R-squared Score (R2): {r2:.4f}")

    if mae > 8.5:
        raise ValueError(f"Model failed acceptance criteria: MAE {mae:.2f} > 8.5 minutes")

    print("\n[SUCCESS] Model passes acceptance criteria (MAE <= 8.5 min)!")

    # Serialize model artifact
    model_path = os.path.join(ARTIFACT_DIR, "relief_model.joblib")
    joblib.dump(model, model_path)
    print(f"Saved model artifact to: {model_path}")

    # Mirror to ml/models/
    mirror_model_path = os.path.join(ML_MODELS_DIR, "relief_model.joblib")
    joblib.dump(model, mirror_model_path)

    # Save metadata
    meta = {
        "model_type": "HistGradientBoostingRegressor",
        "version": "v1.4-rt-gbr",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "mae_minutes": round(float(mae), 3),
        "rmse_minutes": round(float(rmse), 3),
        "r2_score": round(float(r2), 4),
        "target_mae_met": bool(mae <= 8.5),
        "feature_columns": FEATURE_COLUMNS,
        "n_samples": len(X),
    }

    meta_path = os.path.join(ARTIFACT_DIR, "model_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    mirror_meta_path = os.path.join(ML_MODELS_DIR, "model_meta.json")
    with open(mirror_meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta

if __name__ == "__main__":
    train_and_evaluate()
