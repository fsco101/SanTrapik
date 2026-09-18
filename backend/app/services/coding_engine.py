"""
MMDA Unified Vehicular Volume Reduction Program (UVVRP) Rule Engine
Evaluates number coding restrictions and window hour rules across Metro Manila.
Enforces statutory exemptions (motorcycles, public transport).
"""

from datetime import datetime
from typing import Dict, Any, Optional, List

CODING_DAY_MAP = {
    0: {"day": "Monday", "digits": [1, 2]},
    1: {"day": "Tuesday", "digits": [3, 4]},
    2: {"day": "Wednesday", "digits": [5, 6]},
    3: {"day": "Thursday", "digits": [7, 8]},
    4: {"day": "Friday", "digits": [9, 0]},
}

def evaluate_number_coding(
    plate_ending: Optional[int],
    route_name: str,
    current_time: datetime,
    transport_mode: str = "car"
) -> Dict[str, Any]:
    """
    Evaluates whether a commute is subject to MMDA number coding (UVVRP)
    based on day of week, time of day, LGU window hours, and transport mode.
    """
    # 1. Transport Mode Exemptions (Motorcycles, PUVs, Walking)
    if transport_mode in ["motorcycle", "walking", "jeepney"]:
        return {
            "is_coding_active": False,
            "is_restricted": False,
            "plate_ending": plate_ending,
            "restricted_hours": "N/A",
            "restricted_day": "None",
            "has_window_hours": True,
            "window_hours": "Full Exemption",
            "message": f"Transport mode [{transport_mode.upper()}] is legally exempt from MMDA number coding.",
            "affected_corridors": []
        }

    dow = current_time.weekday()
    
    # 2. Weekend Suspension
    if dow >= 5:
        return {
            "is_coding_active": False,
            "is_restricted": False,
            "plate_ending": plate_ending,
            "restricted_hours": "Suspended",
            "restricted_day": "Weekend",
            "has_window_hours": True,
            "window_hours": "All Hours",
            "message": "MMDA number coding is suspended on Saturdays and Sundays.",
            "affected_corridors": []
        }

    day_info = CODING_DAY_MAP[dow]
    day_name = day_info["day"]
    coded_digits = day_info["digits"]

    hour_float = current_time.hour + (current_time.minute / 60.0)

    # MMDA standard peak windows
    in_morning_peak = 7.0 <= hour_float < 10.0
    in_evening_peak = 17.0 <= hour_float < 20.0
    in_window_hours = 10.0 <= hour_float < 17.0

    # Makati has no window hours from 7:00 AM to 7:00 PM
    is_makati_corridor = any(k in route_name.lower() for k in ["makati", "ayala", "buendia", "osmeña"])
    in_makati_restriction = is_makati_corridor and (7.0 <= hour_float < 19.0)

    is_currently_coded_time = in_morning_peak or in_evening_peak or in_makati_restriction

    if plate_ending is None:
        return {
            "is_coding_active": is_currently_coded_time,
            "is_restricted": False,
            "plate_ending": None,
            "restricted_hours": "7:00 AM - 10:00 AM, 5:00 PM - 8:00 PM",
            "restricted_day": day_name,
            "has_window_hours": not is_makati_corridor,
            "window_hours": "10:01 AM - 4:59 PM (Except Makati)",
            "message": f"Today is {day_name}: Vehicles with plates ending in {coded_digits[0]} and {coded_digits[1]} are coded.",
            "affected_corridors": ["EDSA", "C-5", "Roxas Blvd", "Quezon Ave", "Commonwealth", "España"]
        }

    is_plate_coded_today = plate_ending in coded_digits
    is_restricted = is_plate_coded_today and is_currently_coded_time

    if is_restricted:
        if in_makati_restriction and not (in_morning_peak or in_evening_peak):
            msg = f"Plate ending in {plate_ending} is restricted in Makati City (Strict No Window Hours: 7:00 AM - 7:00 PM)."
        else:
            msg = f"Plate ending in {plate_ending} is restricted on {day_name} during peak hours (7-10 AM, 5-8 PM)."
    elif is_plate_coded_today and in_window_hours:
        msg = f"Window hours active (10:01 AM - 4:59 PM): Travel permitted on arterial roads (Caution: Makati enforces no-window rule)."
    elif is_plate_coded_today:
        msg = f"Plate ending in {plate_ending} is coded on {day_name}, but currently outside enforcement hours."
    else:
        msg = f"Plate ending in {plate_ending} is not restricted on {day_name}."

    return {
        "is_coding_active": is_currently_coded_time,
        "is_restricted": is_restricted,
        "plate_ending": plate_ending,
        "restricted_hours": "7:00 AM - 10:00 AM, 5:00 PM - 8:00 PM",
        "restricted_day": day_name,
        "has_window_hours": not is_makati_corridor,
        "window_hours": "10:01 AM - 4:59 PM (Except Makati)",
        "message": msg,
        "affected_corridors": ["EDSA", "C-5", "Roxas Blvd", "Quezon Ave", "Commonwealth", "España"]
    }
