from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.route import (
    RouteRequest,
    RouteAnalyzeResponse,
    RouteAnalyzeData,
    RouteItem,
    GeoJSONLineString,
    TollCostBenefit,
    DelayDecomposition,
    NumberCodingAdvisory,
    FloodHazardDetail
)
from backend.app.services.routing import routing_service
from backend.app.services.spatial import spatial_service
from backend.app.services.toll_calculator import calculate_route_toll, compute_cost_benefit
from backend.app.services.coding_engine import evaluate_number_coding
from backend.app.services.telemetry import telemetry_service
from backend.app.db.session import get_db

router = APIRouter()

@router.post("/route/analyze", response_model=RouteAnalyzeResponse, summary="Analyze Route Traffic & Relief Intelligence")
async def analyze_route(req: RouteRequest, db: Session = Depends(get_db)):
    """
    Core route analysis endpoint:
    1. Determines viable routes via routing engine (OSRM / graph fallback) with multi-modal transport mode.
    2. Segments the route and snaps to Metro Manila road arterials.
    3. Attaches observed speed telemetry, active incidents, travel delays, and AI expected relief time.
    4. Computes expressway Class 1 tolls, economic cost-benefit metrics, MMDA number coding advisory,
       monsoon flood hazard passability, and root cause delay decomposition.
    """
    try:
        raw_routes = await routing_service.get_route(
            origin={"lat": req.origin.lat, "lng": req.origin.lng},
            destination={"lat": req.destination.lat, "lng": req.destination.lng},
            include_alternatives=req.include_alternatives,
            transport_mode=req.transport_mode,
            use_expressway=req.use_expressway
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing service failure: {str(e)}")

    if not raw_routes:
        raise HTTPException(status_code=400, detail="No route could be generated between the specified coordinates.")

    now_manila = telemetry_service.get_manila_now()

    # First pass: evaluate all routes individually
    temp_evaluated = []
    for r in raw_routes:
        coords = r["geometry"]["coordinates"]
        summary, expected_relief, segments, delay_decomp, flood_hazards, is_impassable_flood, spillover_warnings, spillover_segments = spatial_service.analyze_route(
            coords,
            db=db,
            duration_seconds=r.get("duration_seconds"),
            distance_meters=r.get("distance_meters"),
            transport_mode=req.transport_mode
        )

        # Toll calculation: TRB regulations restrict motorcycles <400cc and pedestrians from expressways
        if req.transport_mode in ["motorcycle", "walking"]:
            toll_fee = 0.0
        else:
            toll_fee = calculate_route_toll(coords, r["name"], use_expressway=req.use_expressway)

        # Number coding advisory
        coding_eval = evaluate_number_coding(
            plate_ending=req.plate_ending,
            route_name=r["name"],
            current_time=now_manila,
            transport_mode=req.transport_mode
        )
        coding_adv = NumberCodingAdvisory(
            is_coding_active=coding_eval["is_coding_active"],
            is_restricted=coding_eval["is_restricted"],
            plate_ending=coding_eval.get("plate_ending"),
            restricted_hours=coding_eval.get("restricted_hours", "N/A"),
            restricted_day=coding_eval.get("restricted_day", "None"),
            has_window_hours=coding_eval.get("has_window_hours", True),
            window_hours=coding_eval.get("window_hours", ""),
            message=coding_eval.get("message", ""),
            affected_corridors=coding_eval.get("affected_corridors", [])
        )

        temp_evaluated.append({
            "raw": r,
            "coords": coords,
            "summary": summary,
            "expected_relief": expected_relief,
            "segments": segments,
            "delay_decomp": delay_decomp,
            "flood_hazards": flood_hazards,
            "is_impassable_flood": is_impassable_flood,
            "toll_fee": toll_fee,
            "coding_adv": coding_adv,
            "spillover_warnings": spillover_warnings,
            "spillover_segments": spillover_segments,
        })

    # Second pass: compute comparative toll economics against best zero-toll route
    zero_toll_routes = [it for it in temp_evaluated if it["toll_fee"] == 0.0]
    if zero_toll_routes:
        best_zero_toll = min(zero_toll_routes, key=lambda x: x["summary"].estimated_travel_time_min)
        zero_toll_time = best_zero_toll["summary"].estimated_travel_time_min
        zero_toll_name = best_zero_toll["raw"]["name"]
    else:
        best_zero_toll = min(temp_evaluated, key=lambda x: x["toll_fee"])
        zero_toll_time = best_zero_toll["summary"].estimated_travel_time_min
        zero_toll_name = best_zero_toll["raw"]["name"]

    for item in temp_evaluated:
        toll_fee = item["toll_fee"]
        r_time = item["summary"].estimated_travel_time_min
        cb = compute_cost_benefit(
            expressway_time_min=r_time,
            surface_time_min=zero_toll_time,
            toll_php=toll_fee,
            surface_route_name=zero_toll_name
        )
        item["toll_cost_benefit"] = TollCostBenefit(
            toll_fee_php=toll_fee,
            time_saved_min=cb["time_saved_min"],
            cost_per_min_saved=cb["cost_per_min_saved"],
            comparison_route_name=cb["comparison_route_name"],
            is_zero_toll=(toll_fee == 0.0)
        )

    # Determine Least Traffic (minimum travel time) and Shortest Path (minimum distance)
    min_time = min(it["summary"].estimated_travel_time_min for it in temp_evaluated)
    min_dist = min(it["summary"].total_distance_km for it in temp_evaluated)
    max_time = max(it["summary"].estimated_travel_time_min for it in temp_evaluated)
    max_dist = max(it["summary"].total_distance_km for it in temp_evaluated)

    # Find primary recommended route index (penalize impassable flood, then travel time, then incidents)
    best_idx = 0
    if len(temp_evaluated) > 1:
        best_score = (float("inf"), float("inf"), float("inf"), float("inf"))
        for idx, item in enumerate(temp_evaluated):
            flood_penalty = 1 if item["is_impassable_flood"] else 0
            t = item["summary"].estimated_travel_time_min
            inc = item["summary"].active_incidents_count
            d = item["summary"].total_distance_km
            score = (flood_penalty, t, inc, d)
            if score < best_score:
                best_score = score
                best_idx = idx

    evaluated_routes = []
    for i, item in enumerate(temp_evaluated):
        r = item["raw"]
        summary = item["summary"]
        is_rec = (i == best_idx)

        is_fastest = (summary.estimated_travel_time_min == min_time)
        is_shortest = (summary.total_distance_km == min_dist)

        dist_diff = round(summary.total_distance_km - min_dist, 1)
        time_diff = summary.estimated_travel_time_min - min_time

        toll_cb = item["toll_cost_benefit"]

        if item["is_impassable_flood"]:
            badge = "ALTERNATIVE"
            recommendation_reason = "Caution: Impassable flood hazard detected along corridor. High clearance or detour advised."
        elif len(temp_evaluated) > 1:
            if toll_cb.cost_per_min_saved is not None and toll_cb.time_saved_min > 0:
                badge = "LEAST_TRAFFIC"
                recommendation_reason = f"Fastest Route: Saves {toll_cb.time_saved_min} mins for PHP {int(toll_cb.toll_fee_php)} (PHP {toll_cb.cost_per_min_saved}/min saved)"
            elif is_fastest and is_shortest:
                badge = "LEAST_TRAFFIC_AND_SHORTEST"
                dist_savings = round(max_dist - summary.total_distance_km, 1)
                time_savings = max_time - summary.estimated_travel_time_min
                if dist_savings > 0 and time_savings > 0:
                    recommendation_reason = f"Optimal: Shortest route ({summary.total_distance_km} km) and least traffic ({time_savings} mins faster)"
                else:
                    recommendation_reason = "Optimal: Shortest mileage and fastest free-flow corridor"
            elif is_fastest:
                badge = "LEAST_TRAFFIC"
                savings = max_time - summary.estimated_travel_time_min
                pct = int(round((savings / max_time) * 100)) if max_time > 0 else 0
                recommendation_reason = f"Least Traffic: Saves {savings} mins ({pct}% faster) with rolling average speed {item['segments'][0].average_speed_kmh if item['segments'] else 30} km/h"
            elif is_shortest:
                badge = "SHORTEST_PATH"
                dist_saved = round(max_dist - summary.total_distance_km, 1)
                recommendation_reason = f"Shortest Path: Saves {dist_saved} km in distance (+{time_diff} mins slower due to surface traffic)"
            else:
                badge = "ALTERNATIVE"
                recommendation_reason = f"Alternative Corridor: +{time_diff} mins slower along secondary arterial"
        else:
            badge = "LEAST_TRAFFIC_AND_SHORTEST"
            recommendation_reason = "Optimal route"

        route_item = RouteItem(
            id=r["id"],
            name=r["name"],
            is_recommended=is_rec,
            recommendation_reason=recommendation_reason,
            badge=badge,
            distance_diff_km=dist_diff,
            time_diff_min=time_diff,
            summary=summary,
            expected_relief=item["expected_relief"],
            geometry=GeoJSONLineString(type="LineString", coordinates=item["coords"]),
            segments=item["segments"],
            toll_fee_php=item["toll_fee"],
            toll_cost_benefit=toll_cb,
            delay_decomposition=item["delay_decomp"],
            coding_advisory=item["coding_adv"],
            flood_hazards=item["flood_hazards"],
            is_impassable_flood=item["is_impassable_flood"],
            spillover_warnings=item.get("spillover_warnings", []),
            spillover_segments=item.get("spillover_segments", [])
        )
        evaluated_routes.append(route_item)

        # Register route geometry for active corridor buffer monitoring (<100m alerts)
        from backend.app.services.streaming import stream_manager
        stream_manager.register_route(r["id"], item["coords"])

    now = datetime.now(timezone.utc)
    return RouteAnalyzeResponse(
        status="success",
        data=RouteAnalyzeData(routes=evaluated_routes),
        meta={
            "server_time": now.isoformat(),
            "engine_version": "1.0.0",
            "data_freshness": "live",
            "evaluated_routes_count": len(evaluated_routes)
        }
    )
