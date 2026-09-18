"""
SanTrapik Philippine Expressway Toll Calculation & Economic Optimization Engine
Maintains Class 1 TRB toll rate schedules for Metro Manila expressways:
Skyway Stages 1-3, NAIAX, CAVITEX, SLEX, and NLEX.
Computes commute cost-benefit ratios (PHP per minute saved).
"""

from typing import List, Dict, Any, Optional

# Official TRB Class 1 (Cars, Jeepneys, Vans, Pickups) Toll Rates (in PHP)
EXPRESSWAY_TOLL_RATES: Dict[str, float] = {
    "Skyway Stage 3": 264.0,           # Buendia to Balintawak full bypass
    "Skyway Stage 3 (North)": 129.0,   # Balintawak to Quezon Ave
    "Skyway Stage 3 (South)": 105.0,   # Buendia to Plaza Dilao
    "Skyway Stage 1 & 2": 216.0,       # Buendia to Alabang elevated mainline
    "Skyway Mainline (Sucat)": 172.0,  # Magallanes to Sucat
    "Skyway Mainline (Bicutan)": 130.0,# Magallanes to Bicutan
    "NAIAX": 45.0,                     # NAIA Expressway Airport Connector
    "CAVITEX": 35.0,                   # R-1 Expressway Parañaque to Zapote/Kawit
    "NLEX Open System": 69.0,          # Balintawak to Marilao
    "SLEX At-Grade": 118.0             # Magallanes to Alabang at-grade
}

def calculate_route_toll(
    route_coords: List[List[float]],
    route_name: str,
    use_expressway: bool = True
) -> float:
    """
    Computes total toll fee in PHP for a traversed corridor based on route metadata
    and physical coordinate trajectories.
    """
    if not use_expressway:
        return 0.0

    name_lower = route_name.lower()

    # 1. Direct corridor name matching
    if "skyway stage 3" in name_lower or "stage 3" in name_lower:
        if "balintawak to quezon" in name_lower or "quezon ave" in name_lower and "buendia" not in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Stage 3 (North)"]
        if "plaza dilao" in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Stage 3 (South)"]
        return EXPRESSWAY_TOLL_RATES["Skyway Stage 3"]

    if "skyway" in name_lower:
        if "sucat" in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Mainline (Sucat)"]
        if "bicutan" in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Mainline (Bicutan)"]
        if "alabang" in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Stage 1 & 2"]
        # Default to Stage 3 or Mainline
        return EXPRESSWAY_TOLL_RATES["Skyway Stage 3"]

    if "naiax" in name_lower or "naia expressway" in name_lower or "airport expressway" in name_lower:
        return EXPRESSWAY_TOLL_RATES["NAIAX"]

    if "cavitex" in name_lower or "coastal road" in name_lower:
        return EXPRESSWAY_TOLL_RATES["CAVITEX"]

    if "nlex" in name_lower or "north luzon" in name_lower:
        return EXPRESSWAY_TOLL_RATES["NLEX Open System"]

    if "slex" in name_lower or "south luzon" in name_lower:
        return EXPRESSWAY_TOLL_RATES["SLEX At-Grade"]

    # 2. Coordinate trajectory spatial check for elevated bypasses (e.g. Skyway Stage 3 corridor)
    # Skyway Stage 3 runs north-south between 14.55 and 14.66 near longitude 120.99 - 121.02
    if route_coords and len(route_coords) > 5 and use_expressway:
        has_skyway_lat = any(14.56 <= pt[1] <= 14.64 for pt in route_coords)
        has_skyway_lng = any(120.99 <= pt[0] <= 121.02 for pt in route_coords)
        if has_skyway_lat and has_skyway_lng and "edsa" not in name_lower and "c-5" not in name_lower:
            return EXPRESSWAY_TOLL_RATES["Skyway Stage 3"]

    return 0.0

def compute_cost_benefit(
    expressway_time_min: int,
    surface_time_min: int,
    toll_php: float,
    surface_route_name: str = "Free Surface Route"
) -> Dict[str, Any]:
    """
    Computes economic cost-benefit metrics comparing an expressway route against a free surface road.
    Formula: PHP per minute saved = Toll Fee / Time Saved in Minutes.
    """
    time_saved = max(0, surface_time_min - expressway_time_min)
    cost_per_min = round(toll_php / time_saved, 2) if (toll_php > 0 and time_saved > 0) else None

    return {
        "toll_fee_php": toll_php,
        "time_saved_min": time_saved,
        "cost_per_min_saved": cost_per_min,
        "comparison_route_name": surface_route_name
    }
