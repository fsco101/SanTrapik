from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.telemetry import IncidentListResponse, IncidentItem
from backend.app.db.session import get_db
from backend.app.services.telemetry import telemetry_service

router = APIRouter()

@router.get("/incidents", response_model=IncidentListResponse, summary="List Active & Historical Road Incidents")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, REPORTED, CLEARING, RESOLVED"),
    incident_type: Optional[str] = Query(None, description="Filter by type: ACCIDENT, ROADWORK, FLOOD, STALLED_VEHICLE"),
    db: Session = Depends(get_db)
):
    """
    Returns verified live incidents affecting Metro Manila arterials with exact coordinates,
    severity tiers, and agency source attribution.
    """
    now = datetime.now(timezone.utc)
    raw_items = telemetry_service.get_active_incidents(status=status, severity=None)

    if incident_type:
        raw_items = [i for i in raw_items if i["incident_type"].upper() == incident_type.upper()]

    items = [
        IncidentItem(
            id=item["id"],
            incident_type=item["incident_type"],
            description=item["description"],
            severity=item["severity"],
            status=item["status"],
            lat=item["lat"],
            lng=item["lng"],
            reported_at=item["reported_at"],
            data_source=item["data_source"],
            corridor=item.get("corridor")
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

@router.post("/incidents", summary="Report Live Road Incident")
async def report_incident(payload: Dict[str, Any] = Body(...)):
    """
    Allows commuters, traffic enforcers, and telemetry sensors to report live incidents in real time.
    Coordinates are automatically snapped to the nearest road centerline.
    """
    created = telemetry_service.add_live_incident(payload)
    return {
        "status": "success",
        "message": "Incident reported successfully and snapped to road geometry",
        "data": created
    }

@router.patch("/incidents/{incident_id}/resolve", summary="Resolve / Clear Road Incident")
async def resolve_incident(incident_id: str):
    """
    Allows commuters or traffic enforcers to mark an incident as resolved/cleared in real-time.
    """
    resolved = telemetry_service.resolve_live_incident(incident_id)
    if not resolved:
        return {
            "status": "error",
            "message": f"Incident '{incident_id}' not found in active incidents"
        }
    return {
        "status": "success",
        "message": f"Incident '{incident_id}' marked as RESOLVED and cleared from active corridors",
        "data": resolved
    }

