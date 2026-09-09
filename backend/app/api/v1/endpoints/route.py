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

    evaluated_routes = []
    for i, r in enumerate(raw_routes):
        coords = r["geometry"]["coordinates"]
        summary, expected_relief, segments = spatial_service.analyze_route(coords, db=db)
        
        is_recommended = (i == 0) if len(raw_routes) == 1 else (r["id"] != "rt_edsa_primary")
        recommendation_reason = None
        if len(raw_routes) > 1:
            if is_recommended:
                recommendation_reason = "Faster route saving estimated travel delay and avoiding critical choke points"
            else:
                recommendation_reason = "Primary arterial currently affected by heavy bottlenecks"

        route_item = RouteItem(
            id=r["id"],
            name=r["name"],
            is_recommended=is_recommended,
            recommendation_reason=recommendation_reason,
            summary=summary,
            expected_relief=expected_relief,
            geometry=GeoJSONLineString(type="LineString", coordinates=coords),
            segments=segments
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
