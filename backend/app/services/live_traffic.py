"""
Live Traffic Service for SanTrapik
Integrates real-world Traffic Flow APIs (TomTom / HERE) for Metro Manila corridors,
with automatic fallback to Manila time-based telemetry engine when API keys are omitted.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from backend.app.core.config import settings

logger = logging.getLogger("santrapik.live_traffic")

class LiveTrafficService:
    @property
    def tomtom_key(self) -> Optional[str]:
        return settings.TOMTOM_API_KEY.strip() if settings.TOMTOM_API_KEY else None

    @property
    def here_key(self) -> Optional[str]:
        return settings.HERE_API_KEY.strip() if settings.HERE_API_KEY else None

    def has_live_provider(self) -> bool:
        """Returns True if any live external traffic provider API key is configured."""
        return bool(self.tomtom_key or self.here_key)

    def fetch_tomtom_flow_segment(self, point: List[float]) -> Optional[Dict[str, Any]]:
        """
        Queries TomTom Traffic Flow Segment API for a specific coordinate [lng, lat].
        Returns speed, free-flow speed, and travel time.
        """
        if not self.tomtom_key:
            return None

        lng, lat = point[0], point[1]
        url = (
            f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
            f"?point={lat},{lng}&key={self.tomtom_key}"
        )

        try:
            resp = httpx.get(url, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json().get("flowSegmentData", {})
                current_speed = float(data.get("currentSpeed", 0.0))
                free_flow = float(data.get("freeFlowSpeed", 50.0))
                
                ratio = (current_speed / free_flow) if free_flow > 0 else 1.0
                ratio = min(1.0, max(0.05, ratio))
                congestion_pct = round((1.0 - ratio) * 100.0, 1)

                if ratio >= 0.80:
                    level, color = "NORMAL", "#10B981"
                elif ratio >= 0.50:
                    level, color = "MODERATE", "#F59E0B"
                elif ratio >= 0.25:
                    level, color = "HEAVY", "#F97316"
                else:
                    level, color = "SEVERE", "#EF4444"

                return {
                    "current_speed_kmh": round(current_speed, 1),
                    "baseline_speed_kmh": round(free_flow, 1),
                    "traffic_level": level,
                    "congestion_percentage": congestion_pct,
                    "traffic_color": color,
                    "data_source": "TOMTOM_LIVE_FLOW"
                }
        except Exception as e:
            logger.warning(f"TomTom flow request failed for {point}: {e}")

        return None

    def fetch_here_flow(self, bbox: tuple) -> Optional[List[Dict[str, Any]]]:
        """Queries HERE Traffic Flow API for bounding box if HERE API key is present."""
        if not self.here_key:
            return None

        min_lng, min_lat, max_lng, max_lat = bbox
        url = (
            f"https://data.traffic.hereapi.com/v7/flow"
            f"?in=bbox:{min_lng},{min_lat},{max_lng},{max_lat}"
            f"&locationReferencing=shape&apiKey={self.here_key}"
        )
        try:
            resp = httpx.get(url, timeout=8.0)
            if resp.status_code == 200:
                return resp.json().get("results", [])
        except Exception as e:
            logger.warning(f"HERE flow request failed: {e}")
        return None

    def fetch_tomtom_incidents(self, bbox: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Queries TomTom Traffic Incidents Details API for real-time traffic events,
        roadworks, accidents, and lane closures.
        """
        if not self.tomtom_key:
            return []

        min_lng, min_lat, max_lng, max_lat = bbox or settings.METRO_MANILA_BBOX
        url = (
            f"https://api.tomtom.com/traffic/services/5/incidentDetails"
            f"?bbox={min_lng},{min_lat},{max_lng},{max_lat}"
            f"&language=en-GB&key={self.tomtom_key}"
        )

        incidents: List[Dict[str, Any]] = []
        try:
            resp = httpx.get(url, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                raw_incidents = data.get("incidents", [])
                for item in raw_incidents:
                    geom = item.get("geometry", {})
                    props = item.get("properties", {})
                    coords = geom.get("coordinates", [])

                    # Extract representative point [lng, lat]
                    pt = [121.0, 14.58]
                    if geom.get("type") == "Point" and len(coords) >= 2:
                        pt = [float(coords[0]), float(coords[1])]
                    elif geom.get("type") == "LineString" and len(coords) > 0:
                        mid_idx = len(coords) // 2
                        pt = [float(coords[mid_idx][0]), float(coords[mid_idx][1])]

                    icon_cat = props.get("iconCategory", 0)
                    # Map TomTom iconCategory:
                    # 1: Accident, 7/8/9: Road Works / Closed, 11: Flooding, 14: Stalled/Broken down
                    if icon_cat == 1:
                        inc_type = "ACCIDENT"
                    elif icon_cat in [7, 8, 9]:
                        inc_type = "ROADWORK"
                    elif icon_cat in [4, 11]:
                        inc_type = "FLOOD"
                    elif icon_cat == 14:
                        inc_type = "STALLED_VEHICLE"
                    else:
                        inc_type = "HAZARD"

                    delay_mag = props.get("magnitudeOfDelay", 1)
                    if delay_mag >= 3:
                        sev = "CRITICAL"
                    elif delay_mag == 2:
                        sev = "HIGH"
                    elif delay_mag == 1:
                        sev = "MEDIUM"
                    else:
                        sev = "LOW"

                    # Description & Road info
                    events = props.get("events", [])
                    desc = events[0].get("description", "Traffic incident reported") if events else "Real-time traffic incident"
                    from_str = props.get("from", "")
                    to_str = props.get("to", "")
                    corridor = f"{from_str} to {to_str}".strip(" to ") if (from_str or to_str) else "Metro Manila Corridor"

                    incidents.append({
                        "id": props.get("id", f"inc_tomtom_{len(incidents)}"),
                        "incident_type": inc_type,
                        "description": desc,
                        "severity": sev,
                        "status": "ACTIVE",
                        "point_lng_lat": pt,
                        "corridor": corridor,
                        "minutes_ago": 5,
                        "data_source": "TOMTOM_LIVE_FEED"
                    })
        except Exception as e:
            logger.warning(f"TomTom incidents request failed: {e}")

        return incidents

    def fetch_here_incidents(self, bbox: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Queries HERE Traffic Incidents API if HERE API key is present."""
        if not self.here_key:
            return []

        min_lng, min_lat, max_lng, max_lat = bbox or settings.METRO_MANILA_BBOX
        url = (
            f"https://data.traffic.hereapi.com/v7/incidents"
            f"?in=bbox:{min_lng},{min_lat},{max_lng},{max_lat}"
            f"&apiKey={self.here_key}"
        )
        incidents: List[Dict[str, Any]] = []
        try:
            resp = httpx.get(url, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("results", []):
                    pt = [121.0, 14.58]
                    geom = item.get("location", {}).get("shape", {})
                    # Parse HERE coordinates if available
                    desc = item.get("incidentDetails", {}).get("description", {}).get("value", "Live traffic incident")
                    incidents.append({
                        "id": item.get("id", f"inc_here_{len(incidents)}"),
                        "incident_type": "ACCIDENT" if "accident" in desc.lower() else "HAZARD",
                        "description": desc,
                        "severity": "HIGH",
                        "status": "ACTIVE",
                        "point_lng_lat": pt,
                        "corridor": item.get("location", {}).get("roadName", "Metro Manila Corridor"),
                        "minutes_ago": 5,
                        "data_source": "HERE_LIVE_FEED"
                    })
        except Exception as e:
            logger.warning(f"HERE incidents request failed: {e}")
        return incidents

live_traffic_service = LiveTrafficService()

