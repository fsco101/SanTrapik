"""
SanTrapik Real-Time Telemetry & Traffic Intelligence Service
Computes dynamic, time-varying traffic speeds, congestion levels, and macro-analytics
for Metro Manila arterials based on real-time clock, daylight patterns, and active incidents.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from backend.app.services.live_traffic import live_traffic_service

DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/metro_manila_roads.geojson"))

MANILA_TZ = timezone(timedelta(hours=8))

class RealTimeTelemetryService:
    def __init__(self):
        self._cached_roads: List[Dict[str, Any]] = []
        # Dynamic, real-time verified incident store (no fake synthetic seeds)
        self._live_incidents: List[Dict[str, Any]] = []
        self._load_roads()

    def _load_roads(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self._cached_roads = json.load(f).get("features", [])

    def snap_to_nearest_road(self, lng: float, lat: float, corridor_hint: Optional[str] = None) -> tuple:
        """
        Mathematically snaps any coordinate to the exact centerline of the nearest
        Metro Manila road segment, ensuring incident markers are never floating off-road.
        """
        pt = Point(lng, lat)
        best_dist = float("inf")
        best_point = (lng, lat)
        best_name = corridor_hint or "Metro Manila Corridor"

        for feat in self._cached_roads:
            coords = feat["geometry"]["coordinates"]
            if len(coords) < 2:
                continue
            line = LineString(coords)
            dist = line.distance(pt)
            if dist < best_dist:
                best_dist = dist
                snapped = nearest_points(line, pt)[0]
                best_point = (round(snapped.x, 6), round(snapped.y, 6))
                best_name = feat["properties"].get("road_name", best_name)

        return best_point, best_name

    def get_manila_now(self) -> datetime:
        return datetime.now(MANILA_TZ)

    def calculate_segment_traffic(
        self,
        road_name: str,
        direction: str,
        baseline_speed: float,
        has_incident: bool = False,
        incident_severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates live traffic speed and congestion percentage using real Manila time
        and bottleneck factors.
        """
        now = self.get_manila_now()
        hour = now.hour + (now.minute / 60.0)
        dow = now.weekday()
        is_weekday = dow < 5

        # Rush hour modeling for Metro Manila arterials
        if is_weekday and 7.0 <= hour <= 10.0:
            # Morning Peak: Inbound towards CBDs (SB / WB)
            is_inbound = direction in ["SB", "WB"]
            speed_factor = 0.24 if is_inbound else 0.55
            if any(h in road_name for h in ["Ortigas", "Guadalupe", "Cubao", "Balintawak"]):
                speed_factor *= 0.82
        elif is_weekday and 17.0 <= hour <= 21.0:
            # Evening Peak: Outbound towards residential zones (NB / EB)
            is_outbound = direction in ["NB", "EB"]
            speed_factor = 0.22 if is_outbound else 0.48
            if any(h in road_name for h in ["Ortigas", "Bagong Ilog", "Commonwealth", "Shaw"]):
                speed_factor *= 0.80
        elif 11.0 <= hour <= 16.0:
            # Midday: Moderate commercial traffic
            speed_factor = 0.60
            if "Ortigas" in road_name or "C-5" in road_name:
                speed_factor *= 0.88
        elif 22.0 <= hour or hour <= 5.5:
            # Late Night / Early Morning: Free flow conditions
            speed_factor = 0.92
        else:
            # Shoulder hours (6:00-7:00, 21:00-22:00)
            speed_factor = 0.72

        if not is_weekday:
            # Weekend easing
            speed_factor = min(0.92, speed_factor * 1.30)

        # Incident speed impact
        if has_incident:
            if incident_severity == "CRITICAL":
                speed_factor = min(0.20, speed_factor * 0.25)  # Severe bottleneck due to critical accident
            elif incident_severity == "HIGH":
                speed_factor = min(0.40, speed_factor * 0.50)  # Heavy slowdown due to lane block
            else:
                speed_factor = min(0.60, speed_factor * 0.75)

        speed_factor = max(0.12, min(1.0, speed_factor))
        curr_speed = round(baseline_speed * speed_factor, 1)
        cong_pct = round(max(0.0, min(99.0, (1.0 - speed_factor) * 100.0)), 1)

        if speed_factor >= 0.80:
            level = "NORMAL"
            color = "#10B981"
        elif speed_factor >= 0.50:
            level = "MODERATE"
            color = "#F59E0B"
        elif speed_factor >= 0.25:
            level = "HEAVY"
            color = "#F97316"
        else:
            level = "SEVERE"
            color = "#EF4444"

        return {
            "current_speed_kmh": curr_speed,
            "traffic_level": level,
            "congestion_percentage": cong_pct,
            "traffic_color": color
        }

    def get_live_heatmap_features(self) -> List[Dict[str, Any]]:
        """Generates dynamic GeoJSON heatmap features from real road network."""
        features = []
        now = self.get_manila_now()

        for feat in self._cached_roads:
            props = feat["properties"]
            name = props["road_name"]
            baseline = float(props["baseline_speed_kmh"])
            direction = props.get("direction", "SB")
            seg_coords = feat["geometry"]["coordinates"]
            seg_line = LineString(seg_coords)

            # Match active incident using spatial distance (< ~350m) or corridor substring
            has_inc = False
            inc_sev = None
            for inc in self._live_incidents:
                if inc["status"] != "RESOLVED":
                    inc_pt = Point(inc["point_lng_lat"])
                    corridor_val = inc.get("corridor", "")
                    if seg_line.distance(inc_pt) < 0.0035 or (corridor_val and corridor_val.lower() in name.lower()):
                        has_inc = True
                        inc_sev = inc["severity"]
                        break

            # Check if live external traffic API has real-time speed data for this segment
            live_probe = None
            if live_traffic_service.has_live_provider() and seg_coords:
                mid_pt = seg_coords[len(seg_coords) // 2]
                live_probe = live_traffic_service.fetch_tomtom_flow_segment(mid_pt)

            if live_probe:
                telemetry = live_probe
            else:
                telemetry = self.calculate_segment_traffic(name, direction, baseline, has_inc, inc_sev)

            features.append({
                "type": "Feature",
                "properties": {
                    "road_name": name,
                    "road_code": props.get("road_code"),
                    "direction": direction,
                    "city": props.get("city"),
                    "baseline_speed_kmh": baseline,
                    "current_speed_kmh": telemetry["current_speed_kmh"],
                    "traffic_level": telemetry["traffic_level"],
                    "congestion_percentage": telemetry["congestion_percentage"],
                    "traffic_color": telemetry["traffic_color"],
                    "last_updated": now.isoformat()
                },
                "geometry": feat["geometry"]
            })

        return features

    def get_live_dashboard_stats(self) -> Dict[str, Any]:
        """Dynamically computes aggregate city metrics across all road segments."""
        heatmap = self.get_live_heatmap_features()
        now = self.get_manila_now()

        severe_count = 0
        heavy_count = 0
        moderate_count = 0
        normal_count = 0
        total_speed = 0.0

        for f in heatmap:
            p = f["properties"]
            lvl = p["traffic_level"]
            total_speed += p["current_speed_kmh"]
            if lvl == "SEVERE":
                severe_count += 1
            elif lvl == "HEAVY":
                heavy_count += 1
            elif lvl == "MODERATE":
                moderate_count += 1
            else:
                normal_count += 1

        avg_speed = round(total_speed / len(heatmap), 1) if heatmap else 24.5
        active_incidents = len([inc for inc in self._live_incidents if inc["status"] != "RESOLVED"])

        # Sort top congested corridors
        sorted_congested = sorted(heatmap, key=lambda x: x["properties"]["congestion_percentage"], reverse=True)
        top_congested = []
        for feat in sorted_congested[:4]:
            p = feat["properties"]
            # Compute dynamic relief time estimate
            relief_minutes = int(15 + (p["congestion_percentage"] * 0.35))
            relief_target = now + timedelta(minutes=relief_minutes)
            top_congested.append({
                "road_name": p["road_name"],
                "traffic_level": p["traffic_level"],
                "congestion_percentage": p["congestion_percentage"],
                "average_speed_kmh": p["current_speed_kmh"],
                "expected_relief": relief_target.strftime("%I:%M %p").lstrip("0")
            })

        return {
            "active_incidents": active_incidents,
            "severe_roads_count": severe_count,
            "moderate_roads_count": moderate_count + heavy_count,
            "average_road_speed_kmh": avg_speed,
            "most_congested_roads": top_congested
        }

    def get_active_incidents(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns live incidents with dynamic timestamps relative to real time."""
        now = self.get_manila_now()

        # If live external API provider is configured, synchronize live external incidents
        if live_traffic_service.has_live_provider():
            external_incs = live_traffic_service.fetch_tomtom_incidents() or live_traffic_service.fetch_here_incidents()
            for ext in external_incs:
                if not any(i["id"] == ext["id"] for i in self._live_incidents):
                    snapped_pt, snapped_road = self.snap_to_nearest_road(
                        ext["point_lng_lat"][0], ext["point_lng_lat"][1], ext.get("corridor")
                    )
                    ext["point_lng_lat"] = [snapped_pt[0], snapped_pt[1]]
                    if not ext.get("corridor") or ext["corridor"] == "Metro Manila Corridor":
                        ext["corridor"] = snapped_road
                    self._live_incidents.append(ext)

        results = []
        for inc in self._live_incidents:
            if status and inc["status"].upper() != status.upper():
                continue
            if severity and inc["severity"].upper() != severity.upper():
                continue

            reported_dt = now - timedelta(minutes=inc.get("minutes_ago", 2))
            results.append({
                "id": inc["id"],
                "incident_type": inc["incident_type"],
                "description": inc["description"],
                "severity": inc["severity"],
                "status": inc["status"],
                "lat": inc["point_lng_lat"][1],
                "lng": inc["point_lng_lat"][0],
                "reported_at": reported_dt.isoformat(),
                "data_source": inc.get("data_source", "COMMUTER_LIVE_REPORT"),
                "corridor": inc.get("corridor", "Metro Manila Corridor")
            })

        return results

    def add_live_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allows dynamic incident reporting in real-time with road centerline snapping."""
        now = self.get_manila_now()
        lng = incident_data.get("lng")
        lat = incident_data.get("lat")
        if lng is None or lat is None:
            coords = incident_data.get("point_lng_lat", [121.05, 14.58])
            lng, lat = coords[0], coords[1]

        # Snap to nearest road segment centerline!
        corridor_hint = incident_data.get("road_name") or incident_data.get("corridor")
        snapped_coords, road_name = self.snap_to_nearest_road(float(lng), float(lat), corridor_hint)

        new_inc = {
            "id": incident_data.get("id") or f"inc_live_{int(now.timestamp() * 1000) % 1000000}",
            "incident_type": incident_data.get("incident_type", "ACCIDENT"),
            "description": incident_data.get("description", "Live traffic incident reported by commuter"),
            "severity": incident_data.get("severity", "HIGH"),
            "status": incident_data.get("status", "ACTIVE"),
            "point_lng_lat": [snapped_coords[0], snapped_coords[1]],
            "lat": snapped_coords[1],
            "lng": snapped_coords[0],
            "corridor": road_name,
            "minutes_ago": incident_data.get("minutes_ago", 1),
            "reported_at": now.isoformat(),
            "data_source": incident_data.get("data_source", "COMMUTER_LIVE_REPORT")
        }
        self._live_incidents.insert(0, new_inc)
        return new_inc

    def resolve_live_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Marks a reported live incident as resolved/cleared."""
        for inc in self._live_incidents:
            if str(inc["id"]) == str(incident_id):
                inc["status"] = "RESOLVED"
                return inc
        return None

telemetry_service = RealTimeTelemetryService()
