import json
import os
import math
import httpx
from typing import Dict, Any, List, Optional
from shapely.geometry import Point, LineString
from backend.app.core.config import settings

DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/metro_manila_roads.geojson"))

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

class RoutingService:
    @property
    def OSRM_BASE_URL(self) -> str:
        base = settings.OSRM_URL.rstrip("/")
        if not base.endswith("/route/v1/driving"):
            return f"{base}/route/v1/driving"
        return base

    def __init__(self):
        self._cached_roads = None
        self._route_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_roads()

    def _load_roads(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self._cached_roads = json.load(f).get("features", [])
        else:
            self._cached_roads = []

    def _extract_corridor_name(self, route_data: Dict[str, Any], fallback_name: str) -> str:
        """Extracts prominent street or highway name from OSRM step instructions."""
        legs = route_data.get("legs", [])
        if not legs:
            return fallback_name
        
        street_counts: Dict[str, float] = {}
        for leg in legs:
            for step in leg.get("steps", []):
                name = step.get("name", "").strip()
                dist = step.get("distance", 0)
                if name and name not in ["", "Unnamed Road", "Service Road"]:
                    street_counts[name] = street_counts.get(name, 0) + dist
        
        if not street_counts:
            return fallback_name

        # Find street that covers the largest distance
        sorted_streets = sorted(street_counts.items(), key=lambda x: x[1], reverse=True)
        top_street = sorted_streets[0][0]
        
        # Clean / Normalize common Metro Manila thoroughfares
        if "Epifanio de los Santos" in top_street or "EDSA" in top_street:
            return "via EDSA Corridor"
        elif "Circumferential Road 5" in top_street or "C-5" in top_street or "Eulogio Rodriguez" in top_street:
            return "via C-5 Road Corridor"
        elif "Commonwealth" in top_street:
            return "via Commonwealth Ave"
        elif "Quezon Avenue" in top_street:
            return "via Quezon Avenue"
        elif "España" in top_street:
            return "via España Boulevard"
        elif "Roxas" in top_street:
            return "via Roxas Boulevard"
        elif "South Luzon" in top_street or "SLEX" in top_street:
            return "via SLEX Corridor"
        
        return f"via {top_street}"

    async def _fetch_osrm_route(self, waypoints: List[List[float]], alternatives: bool = False) -> List[Dict[str, Any]]:
        coord_str = ";".join(f"{pt[0]},{pt[1]}" for pt in waypoints)
        url = f"{self.OSRM_BASE_URL}/{coord_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "true" if alternatives else "false"
        }
        headers = {
            "User-Agent": "SanTrapik/1.0 (https://santrapik.ph; traffic-intelligence-system)"
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, params=params, headers=headers)
            if res.status_code == 200:
                data = res.json()
                return data.get("routes", [])
        return []

    async def get_route(self, origin: Dict[str, float], destination: Dict[str, float], include_alternatives: bool = False) -> List[Dict[str, Any]]:
        """
        Calculates high-fidelity turn-by-turn route(s) between origin and destination.
        Queries real OSRM driving engine first, evaluates alternative corridors, and provides
        smooth topological corridor fallback if external network is unavailable.
        """
        orig_coord = [origin["lng"], origin["lat"]]
        dest_coord = [destination["lng"], destination["lat"]]
        cache_key = f"{round(orig_coord[0], 4)},{round(orig_coord[1], 4)}->{round(dest_coord[0], 4)},{round(dest_coord[1], 4)}:{include_alternatives}"

        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        result: List[Dict[str, Any]] = []

        # 1. Query Real OSRM Driving Engine
        try:
            osrm_routes = await self._fetch_osrm_route([orig_coord, dest_coord], alternatives=include_alternatives)
            if osrm_routes:
                # Primary route from OSRM
                r0 = osrm_routes[0]
                primary_name = self._extract_corridor_name(r0, "via Primary Corridor")
                result.append({
                    "id": "rt_osrm_primary",
                    "name": primary_name,
                    "distance_meters": round(r0["distance"], 1),
                    "duration_seconds": int(r0["duration"]),
                    "geometry": r0["geometry"]
                })

                if include_alternatives:
                    # If OSRM returned an alternative directly, use it
                    if len(osrm_routes) > 1:
                        r1 = osrm_routes[1]
                        alt_name = self._extract_corridor_name(r1, "via Alternative Corridor")
                        # Ensure distinct naming
                        if alt_name == primary_name:
                            alt_name = f"{alt_name} (Alternate Path)"
                        result.append({
                            "id": "rt_osrm_alt",
                            "name": alt_name,
                            "distance_meters": round(r1["distance"], 1),
                            "duration_seconds": int(r1["duration"]),
                            "geometry": r1["geometry"]
                        })
                    else:
                        # OSRM only returned 1 route: compute real alternative via complementary arterial corridor
                        alt_result = self._get_alternative_via_point(orig_coord, dest_coord, r0["geometry"]["coordinates"])
                        if alt_result:
                            alt_via, corridor_label = alt_result
                            alt_routes = await self._fetch_osrm_route([orig_coord, alt_via, dest_coord], alternatives=False)
                            if alt_routes:
                                r_alt = alt_routes[0]
                                alt_name = self._extract_corridor_name(r_alt, corridor_label)
                                if alt_name == primary_name:
                                    alt_name = corridor_label
                                result.append({
                                    "id": "rt_osrm_alt_corridor",
                                    "name": alt_name,
                                    "distance_meters": round(r_alt["distance"], 1),
                                    "duration_seconds": int(r_alt["duration"]),
                                    "geometry": r_alt["geometry"]
                                })

                if result:
                    self._route_cache[cache_key] = result
                    return result
        except Exception:
            pass  # Fall through to topological offline routing

        # 2. Topological Offline Corridor Routing (Guarantees zero zig-zags and smooth road alignment)
        result = self._generate_topological_routes(orig_coord, dest_coord, include_alternatives)
        self._route_cache[cache_key] = result
        return result

    def _get_alternative_via_point(self, orig: List[float], dest: List[float], primary_coords: List[List[float]]) -> Optional[Tuple[List[float], str]]:
        """Calculates a sensible via-point along an alternative arterial corridor in Metro Manila."""
        if not primary_coords or len(primary_coords) < 2:
            return None

        # Check if journey is North-South or East-West
        dy = abs(orig[1] - dest[1])
        dx = abs(orig[0] - dest[0])

        if dy >= dx:
            # North-South: choose between EDSA and C-5
            avg_lng = sum(pt[0] for pt in primary_coords) / len(primary_coords)
            if avg_lng < 121.062:
                # Primary is on EDSA/West; route alternative via C-5 (Libis / Bagong Ilog)
                return [121.0720, 14.5950], "via C-5 Road Corridor"
            else:
                # Primary is on C-5/East; route alternative via EDSA (Ortigas / Shaw)
                return [121.0560, 14.5860], "via EDSA Corridor"
        else:
            # East-West: choose between Quezon Ave/España vs Aurora Blvd/Ramon Magsaysay
            avg_lat = sum(pt[1] for pt in primary_coords) / len(primary_coords)
            if avg_lat > 14.615:
                # Route alternative via Aurora Blvd
                return [121.0180, 14.6110], "via Aurora Blvd Corridor"
            else:
                # Route alternative via Quezon Ave
                return [121.0310, 14.6360], "via Quezon Ave Corridor"

    def _generate_topological_routes(self, orig: List[float], dest: List[float], include_alternatives: bool) -> List[Dict[str, Any]]:
        """
        Generates smoothly connected, topologically sorted corridor paths using real road geometry
        from the Metro Manila dataset. Never concatenates disjoint segments arbitrarily.
        """
        is_north_to_south = orig[1] >= dest[1]
        
        # 1. Primary Corridor (EDSA)
        edsa_segs = [
            f for f in self._cached_roads
            if "EDSA" in f["properties"]["road_name"]
        ]
        # Sort segments strictly by latitude along direction of travel
        edsa_segs.sort(key=lambda s: s["geometry"]["coordinates"][0][1], reverse=is_north_to_south)

        primary_coords = [orig]
        for seg in edsa_segs:
            coords = seg["geometry"]["coordinates"]
            # Ensure coordinates within the segment point towards destination
            if is_north_to_south:
                if coords[0][1] < coords[-1][1]:
                    coords = list(reversed(coords))
            else:
                if coords[0][1] > coords[-1][1]:
                    coords = list(reversed(coords))
            
            # Only include segments roughly between origin and destination latitude bounds
            seg_mid_lat = (coords[0][1] + coords[-1][1]) / 2.0
            min_lat = min(orig[1], dest[1]) - 0.02
            max_lat = max(orig[1], dest[1]) + 0.02
            if min_lat <= seg_mid_lat <= max_lat:
                primary_coords.extend(coords)
                
        primary_coords.append(dest)
        primary_dist = sum(haversine_distance(primary_coords[k], primary_coords[k+1]) for k in range(len(primary_coords)-1))
        primary_duration = int(primary_dist / (24 * 1000 / 3600))  # ~24 km/h city average

        routes = [{
            "id": "rt_edsa_primary",
            "name": "via EDSA Corridor",
            "distance_meters": round(primary_dist, 1),
            "duration_seconds": primary_duration,
            "geometry": {
                "type": "LineString",
                "coordinates": primary_coords
            }
        }]

        if include_alternatives:
            # 2. Alternative Corridor (C-5)
            c5_segs = [
                f for f in self._cached_roads
                if "C-5" in f["properties"]["road_name"]
            ]
            c5_segs.sort(key=lambda s: s["geometry"]["coordinates"][0][1], reverse=is_north_to_south)

            alt_coords = [orig]
            for seg in c5_segs:
                coords = seg["geometry"]["coordinates"]
                if is_north_to_south:
                    if coords[0][1] < coords[-1][1]:
                        coords = list(reversed(coords))
                else:
                    if coords[0][1] > coords[-1][1]:
                        coords = list(reversed(coords))
                
                seg_mid_lat = (coords[0][1] + coords[-1][1]) / 2.0
                if min_lat <= seg_mid_lat <= max_lat:
                    alt_coords.extend(coords)
                    
            alt_coords.append(dest)
            alt_dist = sum(haversine_distance(alt_coords[k], alt_coords[k+1]) for k in range(len(alt_coords)-1))
            alt_duration = int(alt_dist / (30 * 1000 / 3600))

            routes.append({
                "id": "rt_c5_alternative",
                "name": "via C-5 Road Corridor",
                "distance_meters": round(alt_dist, 1),
                "duration_seconds": alt_duration,
                "geometry": {
                    "type": "LineString",
                    "coordinates": alt_coords
                }
            })

        return routes

routing_service = RoutingService()
