"""
Feature engineering pipeline for SanTrapik Congestion Relief Prediction.
Extracts normalized temporal, road geometry, speed telemetry, and incident features.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Severity weights
SEVERITY_WEIGHTS = {
    "CRITICAL": 4.0,
    "HIGH": 3.0,
    "MEDIUM": 2.0,
    "LOW": 1.0,
    "NONE": 0.0,
}

FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "is_rush_hour",
    "is_weekend",
    "baseline_speed_kmh",
    "current_speed_kmh",
    "speed_ratio",
    "speed_deficit",
    "congestion_pct",
    "segment_length_m",
    "has_incident",
    "incident_severity_weight",
    "incident_duration_mins",
    "incident_type_collision",
    "incident_type_roadwork",
    "incident_type_flood",
    "incident_type_stall",
]

def encode_temporal_features(dt: Optional[datetime] = None) -> Dict[str, float]:
    """Encodes cyclic time of day and day of week features."""
    if dt is None:
        dt = datetime.now(timezone.utc)

    # Metro Manila is UTC+8
    hour = (dt.hour + 8) % 24 + (dt.minute / 60.0)
    day = dt.weekday() # 0 = Monday, 6 = Sunday

    hour_sin = math.sin(2.0 * math.pi * hour / 24.0)
    hour_cos = math.cos(2.0 * math.pi * hour / 24.0)
    day_sin = math.sin(2.0 * math.pi * day / 7.0)
    day_cos = math.cos(2.0 * math.pi * day / 7.0)

    # Rush hour in Metro Manila: Morning 7:00-10:00 AM, Evening 5:00-9:00 PM
    is_rush_hour = 1.0 if (7.0 <= hour <= 10.0 or 17.0 <= hour <= 21.0) else 0.0
    is_weekend = 1.0 if day in (5, 6) else 0.0

    return {
        "hour_sin": round(hour_sin, 6),
        "hour_cos": round(hour_cos, 6),
        "day_sin": round(day_sin, 6),
        "day_cos": round(day_cos, 6),
        "is_rush_hour": is_rush_hour,
        "is_weekend": is_weekend,
    }

def extract_segment_features(
    baseline_speed: float,
    current_speed: float,
    length_meters: float = 1000.0,
    incident: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> Dict[str, float]:
    """
    Extracts complete 19-dimensional feature vector for a road segment.
    """
    temporal = encode_temporal_features(timestamp)

    base = max(10.0, float(baseline_speed))
    curr = max(2.0, min(float(current_speed), base * 1.5))
    speed_ratio = round(curr / base, 4)
    speed_deficit = max(0.0, round(base - curr, 2))
    congestion_pct = round(max(0.0, min(100.0, (1.0 - speed_ratio) * 100.0)), 2)

    has_incident = 0.0
    sev_weight = 0.0
    inc_duration = 0.0
    is_collision = 0.0
    is_roadwork = 0.0
    is_flood = 0.0
    is_stall = 0.0

    if incident:
        has_incident = 1.0
        sev = str(incident.get("severity", "MEDIUM")).upper()
        sev_weight = SEVERITY_WEIGHTS.get(sev, 2.0)
        inc_duration = float(incident.get("duration_minutes", 15.0))
        inc_type = str(incident.get("type", "")).lower()

        if "collision" in inc_type or "accident" in inc_type:
            is_collision = 1.0
        elif "roadwork" in inc_type or "construction" in inc_type:
            is_roadwork = 1.0
        elif "flood" in inc_type:
            is_flood = 1.0
        elif "stall" in inc_type:
            is_stall = 1.0

    return {
        **temporal,
        "baseline_speed_kmh": round(base, 2),
        "current_speed_kmh": round(curr, 2),
        "speed_ratio": speed_ratio,
        "speed_deficit": speed_deficit,
        "congestion_pct": congestion_pct,
        "segment_length_m": round(float(length_meters), 2),
        "has_incident": has_incident,
        "incident_severity_weight": sev_weight,
        "incident_duration_mins": inc_duration,
        "incident_type_collision": is_collision,
        "incident_type_roadwork": is_roadwork,
        "incident_type_flood": is_flood,
        "incident_type_stall": is_stall,
    }

def features_dict_to_array(f_dict: Dict[str, float]) -> np.ndarray:
    """Converts feature dictionary to ordered numpy array."""
    return np.array([f_dict[col] for col in FEATURE_COLUMNS], dtype=np.float32)

def batch_extract_features(
    segments: List[Dict[str, Any]],
    incidents: Optional[List[Dict[str, Any]]] = None,
    timestamp: Optional[datetime] = None,
) -> np.ndarray:
    """Extracts features for a batch of road segments along a corridor."""
    inc_map = {}
    if incidents:
        for inc in incidents:
            seg_id = inc.get("road_segment_id")
            if seg_id:
                inc_map[seg_id] = inc

    rows = []
    for seg in segments:
        seg_id = seg.get("id") or seg.get("segment_id")
        inc = inc_map.get(seg_id)
        f_dict = extract_segment_features(
            baseline_speed=seg.get("baseline_speed", 50.0),
            current_speed=seg.get("current_speed", 30.0),
            length_meters=seg.get("distance_meters", seg.get("length_meters", 1000.0)),
            incident=inc,
            timestamp=timestamp,
        )
        rows.append(features_dict_to_array(f_dict))

    if not rows:
        return np.empty((0, len(FEATURE_COLUMNS)), dtype=np.float32)
    return np.vstack(rows)
