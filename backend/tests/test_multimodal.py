"""
Sprint 8 Multi-Modal Commuter Intelligence & Corridor Economics Test Suite.
Verifies:
1. SP8-001 (#34): Expressway Toll Calculation Engine & Cost-Benefit Telemetry (Class 1 rates, PHP/min saved).
2. SP8-002 (#35): Motorcycle Telemetry & TRB Rules (lane-filtering speed, 30-50% faster in gridlock, TRB expressway ban).
3. SP8-003 (#36): Monsoon & Flood Hazard Geo-Integration (PAGASA alerts, water depth tiers, detour/impassable flags).
4. SP8-004 (#37): MMDA Number Coding (UVVRP) Rule Engine (plate endings, window hours, Makati strict rule, exemptions).
5. SP8-005 (#38): Chokepoint Root Cause Delay Decomposition (incident, rush volume, weather, and primary cause).
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.toll_calculator import calculate_route_toll, compute_cost_benefit, EXPRESSWAY_TOLL_RATES
from backend.app.services.coding_engine import evaluate_number_coding
from backend.app.services.flood_service import flood_service, CHRONIC_FLOOD_REGISTRY
from backend.app.services.spatial import spatial_service

client = TestClient(app)

# ---------------------------------------------------------------------
# SP8-001: Expressway Toll Calculation & Cost-Benefit Telemetry
# ---------------------------------------------------------------------
def test_toll_matrix_and_rates():
    """Verify TRB Class 1 toll schedule for major Metro Manila expressways."""
    assert EXPRESSWAY_TOLL_RATES["Skyway Stage 3"] == 264.0
    assert EXPRESSWAY_TOLL_RATES["NAIAX"] == 45.0
    assert EXPRESSWAY_TOLL_RATES["CAVITEX"] == 35.0
    assert EXPRESSWAY_TOLL_RATES["NLEX Open System"] == 69.0
    assert EXPRESSWAY_TOLL_RATES["SLEX At-Grade"] == 118.0

    # Direct corridor toll lookups
    coords = [[121.002, 14.657], [121.016, 14.555]]
    assert calculate_route_toll(coords, "via Skyway Stage 3 Bypass", use_expressway=True) == 264.0
    assert calculate_route_toll(coords, "via NAIAX Airport Expressway", use_expressway=True) == 45.0
    assert calculate_route_toll(coords, "via CAVITEX Expressway", use_expressway=True) == 35.0
    assert calculate_route_toll(coords, "via EDSA Corridor", use_expressway=True) == 0.0

    # Expressway toggle off yields zero toll
    assert calculate_route_toll(coords, "via Skyway Stage 3 Bypass", use_expressway=False) == 0.0

def test_cost_benefit_metric_calculation():
    """Verify PHP per minute saved formula: Toll Fee / Time Saved."""
    # Saves 25 minutes for PHP 264.0 -> 264 / 25 = 10.56 PHP/min
    cb = compute_cost_benefit(
        expressway_time_min=20,
        surface_time_min=45,
        toll_php=264.0,
        surface_route_name="via EDSA Corridor"
    )
    assert cb["time_saved_min"] == 25
    assert cb["cost_per_min_saved"] == 10.56
    assert cb["comparison_route_name"] == "via EDSA Corridor"

    # Zero toll route has no cost-per-minute
    cb_free = compute_cost_benefit(
        expressway_time_min=45,
        surface_time_min=45,
        toll_php=0.0
    )
    assert cb_free["time_saved_min"] == 0
    assert cb_free["cost_per_min_saved"] is None

# ---------------------------------------------------------------------
# SP8-002: Motorcycle Telemetry & TRB Rules
# ---------------------------------------------------------------------
def test_motorcycle_trb_expressway_ban():
    """Verify motorcycles <400cc and pedestrians are prohibited from expressways and charged 0 toll."""
    payload = {
        "origin": {"lat": 14.6575, "lng": 121.0020, "name": "Balintawak"},
        "destination": {"lat": 14.5550, "lng": 121.0160, "name": "Makati"},
        "include_alternatives": True,
        "transport_mode": "motorcycle",
        "use_expressway": True  # User attempted to turn on expressway, but motorcycles are restricted
    }
    res = client.post("/api/v1/route/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    routes = data["routes"]
    assert len(routes) >= 1

    for r in routes:
        # Motorcycle routes must strictly have 0 toll
        assert r["toll_fee_php"] == 0.0
        assert r["toll_cost_benefit"]["is_zero_toll"] is True
        # Must not be an elevated expressway
        assert "Skyway Stage 3 Bypass" not in r["name"]

def test_motorcycle_lane_filtering_speed_and_savings():
    """Verify motorcycle lane filtering in gridlock yields 30-50% faster travel times than car."""
    car_payload = {
        "origin": {"lat": 14.6515, "lng": 121.0494, "name": "QC Circle"},
        "destination": {"lat": 14.5573, "lng": 121.0234, "name": "Makati"},
        "include_alternatives": False,
        "transport_mode": "car",
        "use_expressway": False
    }
    car_res = client.post("/api/v1/route/analyze", json=car_payload)
    assert car_res.status_code == 200
    car_route = car_res.json()["data"]["routes"][0]
    car_time = car_route["summary"]["estimated_travel_time_min"]

    moto_payload = {
        **car_payload,
        "transport_mode": "motorcycle"
    }
    moto_res = client.post("/api/v1/route/analyze", json=moto_payload)
    assert moto_res.status_code == 200
    moto_route = moto_res.json()["data"]["routes"][0]
    moto_time = moto_route["summary"]["estimated_travel_time_min"]

    # In congested conditions, motorcycle must be 30% to 50% faster
    savings_pct = (car_time - moto_time) / car_time
    assert 0.28 <= savings_pct <= 0.52, f"Motorcycle savings {savings_pct*100:.1f}% outside 30-50% target range (Car: {car_time}m, Moto: {moto_time}m)"

# ---------------------------------------------------------------------
# SP8-003: Monsoon & Flood Hazard Geo-Integration
# ---------------------------------------------------------------------
def test_flood_hazard_geo_registry():
    """Verify chronic flood registry contains España, Araneta, Balintawak, EDSA Taft, R. Papa."""
    corridor_names = [item["corridor"] for item in CHRONIC_FLOOD_REGISTRY]
    assert any("España" in c for c in corridor_names)
    assert any("Araneta" in c for c in corridor_names)
    assert any("Balintawak" in c for c in corridor_names)
    assert any("EDSA - Taft" in c for c in corridor_names)
    assert any("R. Papa" in c for c in corridor_names)

def test_flood_intersection_and_impassable_flag():
    """Verify route intersecting active España flood is marked impassable to light vehicles."""
    # Trajectory traversing España Blvd near UST [120.9890, 14.6085]
    espana_coords = [
        [120.9850, 14.6050],
        [120.9890, 14.6085],  # UST flood point
        [120.9950, 14.6120]
    ]
    is_impassable, hazards = flood_service.check_route_flooding(espana_coords)
    assert len(hazards) >= 1
    assert hazards[0]["corridor"] == "España Boulevard - UST"
    assert hazards[0]["water_depth"] in ["HALF_TIRE", "TIRE_DEEP", "SUBMERGED"]
    assert is_impassable is True

# ---------------------------------------------------------------------
# SP8-004: MMDA Number Coding (UVVRP) Rule Engine
# ---------------------------------------------------------------------
def test_number_coding_rules_and_exemptions():
    """Verify weekday digit mappings, peak hours, window hours, and exemptions."""
    # Monday: digits 1 and 2
    # 8:30 AM (Peak morning: 7-10 AM)
    mon_peak = datetime(2026, 9, 21, 8, 30)  # 2026-09-21 is Monday
    adv_coded = evaluate_number_coding(plate_ending=1, route_name="via EDSA Corridor", current_time=mon_peak, transport_mode="car")
    assert adv_coded["is_restricted"] is True
    assert adv_coded["is_coding_active"] is True
    assert adv_coded["restricted_day"] == "Monday"

    # Plate ending 3 on Monday is NOT restricted
    adv_uncoded = evaluate_number_coding(plate_ending=3, route_name="via EDSA Corridor", current_time=mon_peak, transport_mode="car")
    assert adv_uncoded["is_restricted"] is False

    # Window hours (1:30 PM: 10:01 AM - 4:59 PM) along EDSA -> Permitted under MMDA window
    mon_window = datetime(2026, 9, 21, 13, 30)
    adv_window = evaluate_number_coding(plate_ending=1, route_name="via EDSA Corridor", current_time=mon_window, transport_mode="car")
    assert adv_window["is_restricted"] is False  # Allowed during window hours on regular MMDA arterials

    # Makati strict rule: NO window hours (7:00 AM - 7:00 PM)
    adv_makati = evaluate_number_coding(plate_ending=1, route_name="via Ayala Makati Corridor", current_time=mon_window, transport_mode="car")
    assert adv_makati["is_restricted"] is True
    assert "Makati" in adv_makati["message"]

    # Statutory exemptions: Motorcycles, PUVs, Walking
    adv_moto = evaluate_number_coding(plate_ending=1, route_name="via EDSA Corridor", current_time=mon_peak, transport_mode="motorcycle")
    assert adv_moto["is_restricted"] is False
    assert "exempt" in adv_moto["message"].lower()

# ---------------------------------------------------------------------
# SP8-005: Chokepoint Root Cause Delay Decomposition
# ---------------------------------------------------------------------
def test_delay_decomposition_sum_and_diagnostics():
    """Verify delay decomposition components sum exactly to total delay and primary cause is identified."""
    payload = {
        "origin": {"lat": 14.6515, "lng": 121.0494, "name": "QC Circle"},
        "destination": {"lat": 14.5573, "lng": 121.0234, "name": "Makati"},
        "include_alternatives": True,
        "transport_mode": "car",
        "use_expressway": True,
        "plate_ending": 1
    }
    res = client.post("/api/v1/route/analyze", json=payload)
    assert res.status_code == 200
    routes = res.json()["data"]["routes"]

    for r in routes:
        decomp = r.get("delay_decomposition")
        assert decomp is not None
        inc_d = decomp["incident_delay_min"]
        vol_d = decomp["baseline_congestion_min"]
        wth_d = decomp["weather_delay_min"]
        tot_d = decomp["total_delay_min"]

        # Mathematical invariance: sum of decomposed delays equals total delay
        assert pytest.approx(inc_d + vol_d + wth_d, abs=0.2) == tot_d
        assert decomp["primary_cause"] in ["INCIDENT", "RUSH_HOUR_VOLUME", "MONSOON_FLOOD", "NORMAL_FLOW"]
        assert len(decomp["cause_details"]) > 0

        # Number coding advisory present
        assert r.get("coding_advisory") is not None

        # Toll cost benefit present
        assert r.get("toll_cost_benefit") is not None
