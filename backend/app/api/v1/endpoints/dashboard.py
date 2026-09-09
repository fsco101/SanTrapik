from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.telemetry import DashboardStatsResponse, DashboardStatsData, CorridorCongestion
from backend.app.db.session import get_db
from backend.app.services.telemetry import telemetry_service

router = APIRouter()

@router.get("/dashboard/stats", response_model=DashboardStatsResponse, summary="Metro Manila Macro-Traffic Analytics")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated city-wide real-time traffic telemetry and dynamically ranked top congested corridors.
    """
    now = datetime.now(timezone.utc)
    stats_dict = telemetry_service.get_live_dashboard_stats()

    top_congested = [
        CorridorCongestion(
            road_name=c["road_name"],
            traffic_level=c["traffic_level"],
            congestion_percentage=c["congestion_percentage"],
            average_speed_kmh=c["average_speed_kmh"],
            expected_relief=c["expected_relief"]
        )
        for c in stats_dict["most_congested_roads"]
    ]

    data = DashboardStatsData(
        active_incidents=stats_dict["active_incidents"],
        severe_roads_count=stats_dict["severe_roads_count"],
        moderate_roads_count=stats_dict["moderate_roads_count"],
        average_road_speed_kmh=stats_dict["average_road_speed_kmh"],
        most_congested_roads=top_congested
    )

    return DashboardStatsResponse(
        status="success",
        data=data,
        meta={
            "server_time": now.isoformat(),
            "region": "Metro Manila, Philippines",
            "data_freshness": "live"
        }
    )
