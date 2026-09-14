from fastapi import APIRouter, Query, Depends, Body, HTTPException, Header, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.telemetry import (
    IncidentListResponse,
    IncidentItem,
    IncidentCreateRequest,
    IncidentCreateResponse,
    IncidentClearanceVoteRequest
)
from backend.app.db.session import get_db
from backend.app.services.telemetry import telemetry_service
from backend.app.core.config import settings

router = APIRouter()

@router.get("/incidents", response_model=IncidentListResponse, summary="List Active & Historical Road Incidents")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, REPORTED, VERIFIED, CLEARING, RESOLVED, EXPIRED"),
    incident_type: Optional[str] = Query(None, description="Filter by type: ACCIDENT, ROADWORK, FLOOD, STALLED_VEHICLE, HAZARD, OTHER"),
    db: Session = Depends(get_db)
):
    """
    Returns verified live incidents affecting Metro Manila arterials with exact coordinates,
    severity tiers, consensus confidence, and agency source attribution.
    """
    now = datetime.now(timezone.utc)
    raw_items = telemetry_service.get_active_incidents(status=status, severity=None)

    if incident_type:
        raw_items = [i for i in raw_items if i["incident_type"].upper() == incident_type.upper()]

    items = [
        IncidentItem(
            id=item["id"],
            incident_type=item["incident_type"],
            description=item.get("description"),
            severity=item["severity"],
            status=item["status"],
            lat=item["lat"],
            lng=item["lng"],
            point_lng_lat=[item["lng"], item["lat"]],
            reported_at=item["reported_at"],
            data_source=item.get("data_source", "COMMUTER_REPORT"),
            corridor=item.get("corridor"),
            confidence=item.get("confidence", 0.75),
            report_count=item.get("report_count", 1),
            still_there_votes=item.get("still_there_votes", 0),
            cleared_votes=item.get("cleared_votes", 0),
            reporter_token=item.get("reporter_token")
        )
        for item in raw_items
    ]

    return IncidentListResponse(
        status="success",
        data=items,
        meta={
            "count": len(items),
            "timestamp": now.isoformat()
        }
    )

@router.post("/incidents", response_model=IncidentCreateResponse, summary="Report Live Road Incident")
async def report_incident(payload: IncidentCreateRequest):
    """
    Allows commuters and emergency services to report live road hazards.
    Payload is validated strictly against Metro Manila bounds and sanitized.
    Coordinates are automatically snapped to the nearest road centerline.
    Returns the created/corroborated incident along with an ephemeral reporter_token.
    """
    created = telemetry_service.add_live_incident(payload.model_dump())
    return IncidentCreateResponse(
        status="success",
        message="Incident reported successfully and snapped to road geometry",
        data=IncidentItem(
            id=created["id"],
            incident_type=created["incident_type"],
            description=created.get("description"),
            severity=created["severity"],
            status=created["status"],
            lat=created["lat"],
            lng=created["lng"],
            point_lng_lat=[created["lng"], created["lat"]],
            reported_at=created["reported_at"],
            data_source=created.get("data_source", "COMMUTER_REPORT"),
            corridor=created.get("corridor"),
            confidence=created.get("confidence", 0.75),
            report_count=created.get("report_count", 1),
            still_there_votes=created.get("still_there_votes", 0),
            cleared_votes=created.get("cleared_votes", 0),
            reporter_token=created.get("reporter_token")
        )
    )

@router.patch("/incidents/{incident_id}/resolve", summary="Resolve / Clear Road Incident")
async def resolve_incident(
    incident_id: str,
    reporter_token: Optional[str] = Query(None, description="Reporter session token for authorization"),
    x_reporter_token: Optional[str] = Header(None, alias="X-Reporter-Token"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
):
    """
    Protected clearance endpoint:
    Only the original author (supplying X-Reporter-Token or query parameter) or an administrator (supplying X-Admin-Key)
    may unilaterally resolve an incident. General users must use POST /incidents/{incident_id}/vote-clearance.
    """
    token = x_reporter_token or reporter_token
    is_admin = bool(x_admin_key and x_admin_key == getattr(settings, "ADMIN_SECRET_KEY", "santrapik_admin_2026"))
    
    success, message, inc = telemetry_service.resolve_live_incident(
        incident_id=incident_id,
        reporter_token=token,
        is_admin=is_admin
    )

    if not inc:
        raise HTTPException(status_code=404, detail=message)
    if not success:
        raise HTTPException(status_code=403, detail=message)

    return {
        "status": "success",
        "message": message,
        "data": inc
    }

@router.post("/incidents/{incident_id}/vote-clearance", summary="Vote on Incident Clearance Status")
async def vote_clearance(incident_id: str, payload: IncidentClearanceVoteRequest):
    """
    Allows commuters to vote whether an incident is STILL_THERE or CLEARED.
    Reaching a net threshold of +3 clear votes transitions the incident to RESOLVED.
    """
    success, message, inc = telemetry_service.cast_clearance_vote(incident_id, payload.vote)
    if not inc:
        raise HTTPException(status_code=404, detail=message)

    return {
        "status": "success" if success else "info",
        "message": message,
        "data": {
            "id": inc["id"],
            "status": inc["status"],
            "cleared_votes": inc.get("cleared_votes", 0),
            "still_there_votes": inc.get("still_there_votes", 0)
        }
    }
