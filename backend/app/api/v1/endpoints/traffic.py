from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.schemas.telemetry import TrafficHeatmapResponse, GeoJSONFeature
from backend.app.db.session import get_db
from backend.app.services.telemetry import telemetry_service

router = APIRouter()

@router.get("/traffic/heatmap", response_model=TrafficHeatmapResponse, summary="Metro Manila Real-Time Traffic Heatmap Layer")
async def get_traffic_heatmap(db: Session = Depends(get_db)):
    """
    Returns GeoJSON FeatureCollection of all monitored arterial road segments in Metro Manila
    with real-time computed speeds, congestion percentages, and traffic colors.
    """
    raw_features = telemetry_service.get_live_heatmap_features()
    features = [
        GeoJSONFeature(
            type="Feature",
            properties=f["properties"],
            geometry=f["geometry"]
        )
        for f in raw_features
    ]

    return TrafficHeatmapResponse(
        type="FeatureCollection",
        features=features
    )
