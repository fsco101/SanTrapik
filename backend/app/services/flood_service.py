"""
Metro Manila Monsoon & Flood Hazard Geo-Integration Service
Maintains geo-registry of chronic flood-prone underpasses and low-lying arteries.
Determines water depth passability tiers (Gutter Deep, Half-Tire, Tire-Deep, Submerged)
and detects impassable corridors for route avoidance.
"""

from typing import List, Dict, Any, Tuple
from shapely.geometry import Point, LineString

# Metric conversion constants at Metro Manila latitude (~14.5 N)
METERS_PER_DEG_LAT = 110600.0
METERS_PER_DEG_LNG = 107500.0

# Chronic Flood-Prone Chokepoints in NCR
CHRONIC_FLOOD_REGISTRY = [
    {
        "id": "fld_espana_ust",
        "corridor": "España Boulevard - UST",
        "city": "Manila",
        "point_lng_lat": [120.9890, 14.6085],
        "default_depth": "HALF_TIRE",
        "description": "Flood waters reached half-tire depth; outer lanes impassable to sedans"
    },
    {
        "id": "fld_araneta_ave",
        "corridor": "Araneta Avenue - Maria Clara",
        "city": "Quezon City",
        "point_lng_lat": [121.0075, 14.6280],
        "default_depth": "TIRE_DEEP",
        "description": "Severe gutter-to-tire flooding from creek overflow; impassable to light vehicles"
    },
    {
        "id": "fld_balintawak_underpass",
        "corridor": "Balintawak Underpass",
        "city": "Quezon City / Caloocan",
        "point_lng_lat": [121.0020, 14.6575],
        "default_depth": "HALF_TIRE",
        "description": "Localized water ponding in vehicular underpass"
    },
    {
        "id": "fld_edsa_taft",
        "corridor": "EDSA - Taft Rotonda",
        "city": "Pasay City",
        "point_lng_lat": [121.0015, 14.5385],
        "default_depth": "GUTTER_DEEP",
        "description": "Gutter deep gutter runoff slow-down near MRT station"
    },
    {
        "id": "fld_rpapa_extension",
        "corridor": "Rizal Avenue Extension - R. Papa",
        "city": "Manila / Caloocan",
        "point_lng_lat": [120.9835, 14.6360],
        "default_depth": "SUBMERGED",
        "description": "Submerged road section; zero passability"
    }
]

class FloodHazardService:
    def __init__(self):
        # By default España and Araneta have seasonal monsoon alerts
        self._active_hazards: List[Dict[str, Any]] = [
            {
                "id": "fld_espana_ust",
                "corridor": "España Boulevard - UST",
                "city": "Manila",
                "lat": 14.6085,
                "lng": 120.9890,
                "water_depth": "HALF_TIRE",
                "passable_to_light": False,
                "status": "ACTIVE",
                "source": "PAGASA / MMDA Monsoon Telemetry",
                "description": "Monsoon rain runoff: Half-tire water level along UST España corridor"
            }
        ]

    def get_active_hazards(self) -> List[Dict[str, Any]]:
        return self._active_hazards

    def check_route_flooding(
        self,
        route_coords: List[List[float]]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Checks whether a route trajectory traverses any active flood hazards within 120 meters.
        Returns:
            (is_impassable_to_light_vehicles, list_of_matching_flood_hazards)
        """
        if not route_coords or len(route_coords) < 2:
            return False, []

        metric_pts = [(pt[0] * METERS_PER_DEG_LNG, pt[1] * METERS_PER_DEG_LAT) for pt in route_coords]
        route_line = LineString(metric_pts)

        matching_hazards = []
        is_impassable = False

        for fld in self._active_hazards:
            if fld.get("status") != "ACTIVE":
                continue
            pt_metric = Point(fld["lng"] * METERS_PER_DEG_LNG, fld["lat"] * METERS_PER_DEG_LAT)
            dist_m = route_line.distance(pt_metric)

            if dist_m <= 150.0:
                matching_hazards.append({
                    **fld,
                    "distance_meters": round(dist_m, 1)
                })
                if fld.get("water_depth") in ["HALF_TIRE", "TIRE_DEEP", "SUBMERGED"]:
                    is_impassable = True

        return is_impassable, matching_hazards

flood_service = FloodHazardService()
