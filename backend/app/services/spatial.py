import json
import os
import time
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import LineString, Point
from sqlalchemy.orm import Session

from backend.app.db.models import RoadSegment, TrafficRecord, Incident, Prediction
from backend.app.schemas.route import (
    RouteSegmentDetail,
    IncidentSummary,
    SegmentPrediction,
    RouteSummary,
    ExpectedRelief,
    DelayDecomposition,
    FloodHazardDetail
)
from backend.app.ml.inference import prediction_service
from backend.app.services.telemetry import telemetry_service, DATA_FILE
from backend.app.services.flood_service import flood_service

def haversine_distance(coord1: List[float], coord2: List[float]) -> float:
    """Calculate distance in meters between two [lng, lat] coordinates."""
    lng1, lat1 = coord1
    lng2, lat2 = coord2
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class SpatialService:
    _db_healthy: bool = True
    _last_db_check: float = 0.0

    def __init__(self):
        self._cached_roads = None
        self._load_cached_roads()

    def _load_cached_roads(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self._cached_roads = json.load(f).get("features", [])
        else:
            self._cached_roads = []

    def analyze_route(
        self,
        route_coords: List[List[float]],
        db: Session = None,
        duration_seconds: Optional[int] = None,
        distance_meters: Optional[float] = None,
        transport_mode: str = "car"
    ) -> Tuple[RouteSummary, ExpectedRelief, List[RouteSegmentDetail], DelayDecomposition, List[FloodHazardDetail], bool]:
        """
        Decomposes real route geometry into constituent Metro Manila road segments,
        calculates live travel times and delay based on real-time traffic telemetry and transport mode,
        evaluates motorcycle lane-filtering dynamics, flood hazard passability, delay decomposition,
        and invokes the ML model to forecast congestion relief duration.
        """
        route_line = LineString(route_coords)
        now = telemetry_service.get_manila_now()
        now_ts = time.time()
        
        # Buffer distance in degrees (~120 meters)
        buffer_deg = 0.0011

        matched_segments: List[RouteSegmentDetail] = []
        ml_segment_inputs: List[Dict[str, Any]] = []
        ml_incident_inputs: List[Dict[str, Any]] = []

        # 1. Spatial Matching along Monitored Corridors
        active_incidents = telemetry_service.get_active_incidents(status="ACTIVE")

        if self._cached_roads:
            # Check traversed segments in geographical sequence
            candidate_segments = []
            for feat in self._cached_roads:
                props = feat["properties"]
                geom = feat["geometry"]
                seg_coords = geom["coordinates"]
                seg_line = LineString(seg_coords)
                
                # If route intersects or runs parallel within ~120m
                if route_line.distance(seg_line) < buffer_deg:
                    # Projection distance along route to preserve travel sequence
                    proj_dist = route_line.project(Point(seg_coords[0]))
                    candidate_segments.append((proj_dist, feat, seg_line))

            # Sort candidate segments by appearance along the route
            candidate_segments.sort(key=lambda x: x[0])

            for _, feat, seg_line in candidate_segments:
                props = feat["properties"]
                name = props["road_name"]
                direction = props.get("direction", "SB")
                baseline = float(props["baseline_speed_kmh"])

                # Check active incidents intersecting this segment
                seg_incidents: List[IncidentSummary] = []
                has_inc = False
                max_sev = None

                for inc in active_incidents:
                    inc_pt = Point(inc["lng"], inc["lat"])
                    if seg_line.distance(inc_pt) < 0.0015:
                        has_inc = True
                        max_sev = inc["severity"]
                        seg_incidents.append(IncidentSummary(
                            id=inc["id"],
                            type=inc["incident_type"],
                            severity=inc["severity"],
                            description=inc["description"],
                            reported_at=inc["reported_at"],
                            status=inc["status"]
                        ))
                        if not any(item.get("id") == inc["id"] for item in ml_incident_inputs):
                            ml_incident_inputs.append({
                                "id": inc["id"],
                                "road_segment_id": props.get("road_code", name),
                                "type": inc["incident_type"],
                                "severity": inc["severity"],
                                "duration_minutes": 25.0
                            })

                # Compute real-time speed and congestion
                live_telemetry = telemetry_service.calculate_segment_traffic(
                    name, direction, baseline, has_incident=has_inc, incident_severity=max_sev
                )
                speed = live_telemetry["current_speed_kmh"]
                level = live_telemetry["traffic_level"]
                cong = live_telemetry["congestion_percentage"]

                # Motorcycle lane-filtering physics:
                # In gridlock (cong >= 40% or car speed < 20 km/h), motorcycles filter at 26-32 km/h
                if transport_mode == "motorcycle" and cong >= 40.0:
                    speed = round(min(35.0, max(speed, 26.0 + (cong * 0.05))), 1)

                # Calculate physical segment length in meters
                seg_coords = feat["geometry"]["coordinates"]
                seg_length_m = sum(haversine_distance(seg_coords[k], seg_coords[k+1]) for k in range(len(seg_coords)-1))

                ml_segment_inputs.append({
                    "id": props.get("road_code", name),
                    "current_speed": speed,
                    "baseline_speed": baseline,
                    "distance_meters": max(200.0, seg_length_m)
                })

                pred_mins = int(12 + (cong * 0.32))
                pred_time = (now + timedelta(minutes=pred_mins)).strftime("%I:%M %p").lstrip("0")

                matched_segments.append(RouteSegmentDetail(
                    segment_id=f"seg_{abs(hash(name)) % 100000}",
                    name=name,
                    road_code=props.get("road_code"),
                    direction=direction,
                    traffic_level=level,
                    average_speed_kmh=speed,
                    congestion_percentage=cong,
                    incidents=seg_incidents,
                    prediction=SegmentPrediction(
                        predicted_relief_time=pred_time,
                        predicted_relief_minutes=pred_mins,
                        confidence=0.84 if level in ["SEVERE", "HEAVY"] else 0.90
                    ),
                    last_updated=(now - timedelta(minutes=2)).strftime("%I:%M %p").lstrip("0")
                ))

        # Fallback if route does not intersect monitored arterials
        if not matched_segments:
            fallback_speed = 32.0 if transport_mode != "motorcycle" else 35.0
            matched_segments.append(RouteSegmentDetail(
                segment_id="seg_primary_corridor",
                name="Traversed Metro Manila Arterial",
                road_code="NCR",
                direction="BOTH",
                traffic_level="MODERATE",
                average_speed_kmh=fallback_speed,
                congestion_percentage=45.0,
                incidents=[],
                prediction=SegmentPrediction(
                    predicted_relief_time=(now + timedelta(minutes=20)).strftime("%I:%M %p").lstrip("0"),
                    predicted_relief_minutes=20,
                    confidence=0.85
                ),
                last_updated=now.strftime("%I:%M %p").lstrip("0")
            ))
            ml_segment_inputs.append({
                "id": "seg_primary",
                "current_speed": fallback_speed,
                "baseline_speed": 55.0,
                "distance_meters": 5000.0
            })

        # 2. Accurate Distance & Duration Calculation
        if distance_meters and distance_meters > 0:
            total_dist_km = round(distance_meters / 1000.0, 1)
        else:
            actual_dist_m = sum(haversine_distance(route_coords[k], route_coords[k+1]) for k in range(len(route_coords)-1))
            total_dist_km = round(actual_dist_m / 1000.0, 1)

        # 3. Flood Hazard Geo-Integration
        is_impassable_flood, active_flood_hazards = flood_service.check_route_flooding(route_coords)
        flood_hazard_details = [
            FloodHazardDetail(
                id=f["id"],
                corridor=f["corridor"],
                city=f["city"],
                water_depth=f.get("water_depth", "HALF_TIRE"),
                passable_to_light=f.get("passable_to_light", False),
                description=f.get("description"),
                distance_meters=f.get("distance_meters")
            )
            for f in active_flood_hazards
        ]

        # Calculate travel time according to transport mode
        avg_cong = sum(s.congestion_percentage for s in matched_segments) / len(matched_segments)

        if transport_mode == "walking":
            # Walking pace ~4.8 km/h regardless of vehicular traffic jams
            normal_travel_time_min = max(3, int(round((total_dist_km / 4.8) * 60)))
            estimated_travel_time_min = normal_travel_time_min
            overall_congestion = "NORMAL"
        elif transport_mode == "motorcycle":
            # Motorcycle lane filtering: in gridlock (avg_cong >= 25%), filtering at 26-32 km/h
            # yields empirical 30% to 50% travel time savings over cars.
            speed_cap = 45.0
            normal_travel_time_min = max(3, int(round((total_dist_km / speed_cap) * 60)))

            # Car travel time baseline for comparison
            car_cong_multiplier = 1.0 + (avg_cong / 100.0) * 0.95
            if duration_seconds and duration_seconds > 0:
                car_time = max(max(3, int(round((total_dist_km / 50.0) * 60))), int(round((duration_seconds / 60.0) * car_cong_multiplier)))
            else:
                car_normal = max(3, int(round((total_dist_km / 50.0) * 60)))
                car_time = max(car_normal, int(round(car_normal * car_cong_multiplier)))

            if avg_cong >= 25.0:
                # 30% to 45% time savings over car
                savings_ratio = min(0.45, max(0.30, 0.25 + (avg_cong / 100.0) * 0.20))
                estimated_travel_time_min = max(normal_travel_time_min, int(round(car_time * (1.0 - savings_ratio))))
            else:
                cong_multiplier = 1.0 + (avg_cong / 100.0) * 0.35
                base_min = (duration_seconds / 60.0) if (duration_seconds and duration_seconds > 0) else normal_travel_time_min
                estimated_travel_time_min = max(normal_travel_time_min, int(round(base_min * cong_multiplier)))
        elif transport_mode == "jeepney":
            # Jeepneys have frequent curb stops and dwell times
            speed_cap = 30.0
            normal_travel_time_min = max(3, int(round((total_dist_km / speed_cap) * 60)))
            cong_multiplier = 1.0 + (avg_cong / 100.0) * 1.30
            base_min = (duration_seconds / 60.0) if (duration_seconds and duration_seconds > 0) else normal_travel_time_min
            estimated_travel_time_min = max(normal_travel_time_min, int(round(base_min * 1.25 * cong_multiplier)))
        else:  # car
            speed_cap = 50.0
            normal_travel_time_min = max(3, int(round((total_dist_km / speed_cap) * 60)))
            cong_multiplier = 1.0 + (avg_cong / 100.0) * 0.95
            base_min = (duration_seconds / 60.0) if (duration_seconds and duration_seconds > 0) else normal_travel_time_min
            estimated_travel_time_min = max(normal_travel_time_min, int(round(base_min * cong_multiplier)))

        # Flood impact on travel time
        if flood_hazard_details:
            if is_impassable_flood:
                estimated_travel_time_min += 15  # Detour penalty
            else:
                estimated_travel_time_min += 6   # Monsoon waterlogging slowdown

        estimated_delay_min = max(0, estimated_travel_time_min - normal_travel_time_min)

        # Overall Congestion Rating
        if avg_cong >= 70.0 or any(s.traffic_level == "SEVERE" for s in matched_segments):
            overall_congestion = "SEVERE"
        elif avg_cong >= 50.0 or any(s.traffic_level == "HEAVY" for s in matched_segments):
            overall_congestion = "HEAVY"
        elif avg_cong >= 30.0:
            overall_congestion = "MODERATE"
        else:
            overall_congestion = "NORMAL"

        # Most Affected Segment
        sorted_by_cong = sorted(matched_segments, key=lambda s: s.congestion_percentage, reverse=True)
        most_affected_segment = sorted_by_cong[0].name if sorted_by_cong else "NCR Arterial Corridor"

        unique_incident_ids = {inc.id for s in matched_segments for inc in s.incidents}
        total_active_incidents = len(unique_incident_ids)

        summary = RouteSummary(
            total_distance_km=total_dist_km,
            estimated_travel_time_min=estimated_travel_time_min,
            normal_travel_time_min=normal_travel_time_min,
            estimated_delay_min=estimated_delay_min,
            overall_congestion=overall_congestion,
            active_incidents_count=total_active_incidents,
            most_affected_segment=most_affected_segment
        )

        # 4. Delay Decomposition Diagnostics
        total_delay_float = float(estimated_delay_min)
        if total_delay_float <= 0:
            delay_decomp = DelayDecomposition(
                incident_delay_min=0.0,
                baseline_congestion_min=0.0,
                weather_delay_min=0.0,
                total_delay_min=0.0,
                primary_cause="NORMAL_FLOW",
                cause_details="Free-flow vehicular speeds along traversed corridor."
            )
        else:
            raw_weather = 0.0
            if flood_hazard_details:
                for fld in flood_hazard_details:
                    if fld.water_depth in ["SUBMERGED", "TIRE_DEEP"]:
                        raw_weather += 12.0
                    elif fld.water_depth == "HALF_TIRE":
                        raw_weather += 8.0
                    else:
                        raw_weather += 4.0

            raw_incident = 0.0
            for inc_id in unique_incident_ids:
                matching_inc = next((i for s in matched_segments for i in s.incidents if i.id == inc_id), None)
                if matching_inc:
                    sev = matching_inc.severity.upper()
                    if sev == "CRITICAL":
                        raw_incident += 14.0
                    elif sev == "HIGH":
                        raw_incident += 9.0
                    elif sev == "MODERATE":
                        raw_incident += 5.0
                    else:
                        raw_incident += 3.0

            # Scale and allocate components within total delay
            incident_delay = min(total_delay_float, raw_incident)
            rem = total_delay_float - incident_delay
            weather_delay = min(rem, raw_weather)
            baseline_congestion = max(0.0, total_delay_float - incident_delay - weather_delay)

            incident_delay = round(incident_delay, 1)
            weather_delay = round(weather_delay, 1)
            baseline_congestion = round(total_delay_float - incident_delay - weather_delay, 1)
            if baseline_congestion < 0:
                baseline_congestion = 0.0
                weather_delay = round(total_delay_float - incident_delay, 1)

            # Determine primary cause
            causes = [
                ("INCIDENT", incident_delay),
                ("MONSOON_FLOOD", weather_delay),
                ("RUSH_HOUR_VOLUME", baseline_congestion)
            ]
            causes.sort(key=lambda x: x[1], reverse=True)
            primary_cause = causes[0][0]

            parts = []
            if incident_delay > 0:
                parts.append(f"Active incident bottlenecks (+{incident_delay}m)")
            if weather_delay > 0:
                parts.append(f"Monsoon waterlogging & slow runoff (+{weather_delay}m)")
            if baseline_congestion > 0:
                parts.append(f"Rush-hour commuter volume (+{baseline_congestion}m)")

            cause_details = "; ".join(parts) if parts else "Recurrent corridor congestion."

            delay_decomp = DelayDecomposition(
                incident_delay_min=incident_delay,
                baseline_congestion_min=baseline_congestion,
                weather_delay_min=weather_delay,
                total_delay_min=round(total_delay_float, 1),
                primary_cause=primary_cause,
                cause_details=cause_details
            )

        # 5. AI / ML Congestion Relief Forecast
        ml_prediction = prediction_service.predict_corridor_relief(
            segments=ml_segment_inputs,
            incidents=ml_incident_inputs,
            timestamp=now
        )

        relief_minutes = ml_prediction["predicted_relief_minutes"]
        relief_target_dt = now + timedelta(minutes=relief_minutes)
        relief_time_iso = relief_target_dt.isoformat()

        expected_relief = ExpectedRelief(
            relief_time=relief_time_iso,
            estimated_minutes_remaining=relief_minutes,
            confidence=ml_prediction["confidence_score"],
            confidence_interval=ml_prediction.get("confidence_interval"),
            is_predicted=True,
            model_version=ml_prediction.get("model_version", "v1.4-rt-gbr")
        )

        return summary, expected_relief, matched_segments, delay_decomp, flood_hazard_details, is_impassable_flood

spatial_service = SpatialService()
