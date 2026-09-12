from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.route import RouteRequest, RouteAnalyzeResponse, RouteAnalyzeData, RouteItem, GeoJSONLineString
from backend.app.services.routing import routing_service
from backend.app.services.spatial import spatial_service
from backend.app.db.session import get_db

router = APIRouter()

@router.post("/route/analyze", response_model=RouteAnalyzeResponse, summary="Analyze Route Traffic & Relief Intelligence")
async def analyze_route(req: RouteRequest, db: Session = Depends(get_db)):
    """
    Core route analysis endpoint:
    1. Determines viable routes via routing engine (OSRM / graph fallback).
    2. Segments the route and snaps to Metro Manila road arterials.
    3. Attaches observed speed telemetry, active incidents, travel delays, and AI expected relief time.
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

    # First pass: evaluate all routes
    temp_evaluated = []
    for r in raw_routes:
        coords = r["geometry"]["coordinates"]
        summary, expected_relief, segments = spatial_service.analyze_route(
            coords,
            db=db,
            duration_seconds=r.get("duration_seconds"),
            distance_meters=r.get("distance_meters"),
            transport_mode=req.transport_mode
        )
        temp_evaluated.append({
            "raw": r,
            "coords": coords,
            "summary": summary,
            "expected_relief": expected_relief,
            "segments": segments,
        })

    # Determine Least Traffic (minimum travel time) and Shortest Path (minimum distance)
    min_time = min(it["summary"].estimated_travel_time_min for it in temp_evaluated)
    min_dist = min(it["summary"].total_distance_km for it in temp_evaluated)
    max_time = max(it["summary"].estimated_travel_time_min for it in temp_evaluated)
    max_dist = max(it["summary"].total_distance_km for it in temp_evaluated)

    # Find primary recommended route index (least travel time, tie-breaker: fewer incidents, then shorter distance)
    best_idx = 0
    if len(temp_evaluated) > 1:
        best_score = (float("inf"), float("inf"), float("inf"))
        for idx, item in enumerate(temp_evaluated):
            t = item["summary"].estimated_travel_time_min
            inc = item["summary"].active_incidents_count
            d = item["summary"].total_distance_km
            score = (t, inc, d)
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

        if len(temp_evaluated) > 1:
            if is_fastest and is_shortest:
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
            segments=item["segments"]
        )
        evaluated_routes.append(route_item)

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
