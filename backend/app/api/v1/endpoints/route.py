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
            include_alternatives=req.include_alternatives
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing service failure: {str(e)}")

    if not raw_routes:
        raise HTTPException(status_code=400, detail="No route could be generated between the specified coordinates.")

    # First pass: evaluate all routes
    temp_evaluated = []
    for r in raw_routes:
        coords = r["geometry"]["coordinates"]
        summary, expected_relief, segments = spatial_service.analyze_route(coords, db=db)
        temp_evaluated.append({
            "raw": r,
            "coords": coords,
            "summary": summary,
            "expected_relief": expected_relief,
            "segments": segments,
        })

    # Find the best route (lowest estimated travel time; tie-breaker: fewer incidents)
    best_idx = 0
    if len(temp_evaluated) > 1:
        best_time = float("inf")
        best_inc = float("inf")
        for idx, item in enumerate(temp_evaluated):
            t = item["summary"].estimated_travel_time_min
            inc = item["summary"].active_incidents_count
            if t < best_time or (t == best_time and inc < best_inc):
                best_time = t
                best_inc = inc
                best_idx = idx

    evaluated_routes = []
    base_best_time = temp_evaluated[best_idx]["summary"].estimated_travel_time_min

    for i, item in enumerate(temp_evaluated):
        r = item["raw"]
        summary = item["summary"]
        is_rec = (i == best_idx)

        if len(temp_evaluated) > 1:
            if is_rec:
                # Find worst time to calculate savings
                other_times = [it["summary"].estimated_travel_time_min for j, it in enumerate(temp_evaluated) if j != i]
                max_other = max(other_times) if other_times else summary.estimated_travel_time_min
                savings = max(0, max_other - summary.estimated_travel_time_min)
                pct = int(round((savings / max_other) * 100)) if max_other > 0 else 0
                inc_count = summary.active_incidents_count
                if savings > 0:
                    recommendation_reason = f"Recommended: Saves {savings} mins ({pct}% faster) with {inc_count} active incidents"
                else:
                    recommendation_reason = f"Recommended: Optimal corridor with fewer congestion bottlenecks"
            else:
                delay_delta = summary.estimated_travel_time_min - base_best_time
                recommendation_reason = f"+{delay_delta} mins slower due to heavy congestion along corridor"
        else:
            recommendation_reason = "Optimal route"

        route_item = RouteItem(
            id=r["id"],
            name=r["name"],
            is_recommended=is_rec,
            recommendation_reason=recommendation_reason,
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
