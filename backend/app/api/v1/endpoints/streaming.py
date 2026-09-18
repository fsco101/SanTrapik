from fastapi import APIRouter, Request, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from backend.app.services.streaming import stream_manager
from backend.app.services.telemetry import telemetry_service
from backend.app.core.spatial_guardrails import validate_philippine_coordinate

router = APIRouter()

class SubscriptionUpdateRequest(BaseModel):
    min_lng: Optional[float] = Field(None, description="Minimum longitude for visible viewport")
    min_lat: Optional[float] = Field(None, description="Minimum latitude for visible viewport")
    max_lng: Optional[float] = Field(None, description="Maximum longitude for visible viewport")
    max_lat: Optional[float] = Field(None, description="Maximum latitude for visible viewport")
    route_id: Optional[str] = Field(None, description="Active route ID for chokepoint buffer monitoring")

@router.get("/telemetry/stream", summary="High-Throughput Viewport-Filtered Server-Sent Events (SSE) Stream")
async def stream_telemetry(
    request: Request,
    min_lng: Optional[float] = Query(None, description="Bounding box min longitude"),
    min_lat: Optional[float] = Query(None, description="Bounding box min latitude"),
    max_lng: Optional[float] = Query(None, description="Bounding box max longitude"),
    max_lat: Optional[float] = Query(None, description="Bounding box max latitude"),
    route_id: Optional[str] = Query(None, description="Active analyzed route ID for chokepoint buffer alerts"),
    client_id: Optional[str] = Query(None, description="Optional custom client session ID")
):
    """
    Persistent HTTP Server-Sent Events (SSE) gateway emitting real-time geospatial deltas:
    - Automated 15-second keepalive pings (: keepalive)
    - Viewport filtering (SP7-002): delivers events intersecting client visible bbox
    - Route corridor alerts (SP7-003): emits high-priority 'route_obstruction' if incident occurs within 100m of route
    - Coroutine safe & leak-free client disconnect cleanup
    """
    bbox: Optional[Tuple[float, float, float, float]] = None
    if any(v is not None for v in (min_lng, min_lat, max_lng, max_lat)):
        if any(v is None for v in (min_lng, min_lat, max_lng, max_lat)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All 4 bounding box coordinates (min_lng, min_lat, max_lng, max_lat) must be supplied together."
            )
        if min_lng > max_lng or min_lat > max_lat:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid bounding box: min coordinates must be <= max coordinates."
            )
        bbox = (min_lng, min_lat, max_lng, max_lat)

    subscriber = await stream_manager.register_subscriber(
        client_id=client_id,
        bbox=bbox,
        route_id=route_id
    )

    return StreamingResponse(
        stream_manager.stream_events(subscriber, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/telemetry/stream/{client_id}/subscription", summary="Renegotiate Client Viewport BBox or Active Route")
async def update_subscription(
    client_id: str,
    payload: SubscriptionUpdateRequest
):
    """
    Allows a connected client to update their visible map viewport or active route subscription
    as they pan, zoom, or recalculate routes, without severing the persistent SSE stream.
    """
    bbox: Optional[Tuple[float, float, float, float]] = None
    if any(v is not None for v in (payload.min_lng, payload.min_lat, payload.max_lng, payload.max_lat)):
        if any(v is None for v in (payload.min_lng, payload.min_lat, payload.max_lng, payload.max_lat)):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="All 4 bbox coordinates must be provided together."
            )
        if payload.min_lng > payload.max_lng or payload.min_lat > payload.max_lat:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min coordinates cannot exceed max coordinates."
            )
        bbox = (payload.min_lng, payload.min_lat, payload.max_lng, payload.max_lat)

    updated = await stream_manager.update_subscriber_subscription(
        client_id=client_id,
        bbox=bbox,
        route_id=payload.route_id
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscriber '{client_id}' not found. Connect to /api/v1/telemetry/stream first."
        )

    return {
        "status": "success",
        "message": f"Subscription for client '{client_id}' updated successfully.",
        "data": {
            "client_id": client_id,
            "bbox": bbox,
            "route_id": payload.route_id
        }
    }

@router.get("/traffic/speed-deltas", summary="Get Current Road Velocity Deltas")
async def get_speed_deltas():
    """
    Returns lightweight speed delta patches for monitored Metro Manila segments
    allowing instant initialization before stream deltas arrive.
    """
    deltas = telemetry_service.get_live_velocity_deltas()
    return {
        "status": "success",
        "data": deltas,
        "meta": {
            "count": len(deltas),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
