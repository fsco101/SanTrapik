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

live_traffic_service = LiveTrafficService()
