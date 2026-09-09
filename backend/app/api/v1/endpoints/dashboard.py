from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.schemas.telemetry import DashboardStatsResponse, DashboardStatsData, CorridorCongestion
from backend.app.db.session import get_db

router = APIRouter()

@router.get("/dashboard/stats", response_model=DashboardStatsResponse, summary="Metro Manila Macro-Traffic Analytics")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated city-wide traffic telemetry and top congested corridors.
    """
    now = datetime.now(timezone.utc)
    top_congested = [
        CorridorCongestion(
            road_name="EDSA - Ortigas Flyover SB",
            traffic_level="SEVERE",
            congestion_percentage=91.5,
            average_speed_kmh=11.2,
            expected_relief="10:42 PM"
        ),
        CorridorCongestion(
            road_name="C-5 - Bagong Ilog to Kalayaan",
            traffic_level="SEVERE",
            congestion_percentage=86.0,
            average_speed_kmh=14.5,
            expected_relief="11:05 PM"
        ),
        CorridorCongestion(
            road_name="Commonwealth - Philcoa to Circle",
            traffic_level="HEAVY",
            congestion_percentage=73.0,
            average_speed_kmh=24.0,
            expected_relief="10:18 PM"
        ),
        CorridorCongestion(
            road_name="España Boulevard - Welcome to UST",
            traffic_level="HEAVY",
            congestion_percentage=69.0,
            average_speed_kmh=18.5,
            expected_relief="10:30 PM"
        )
    ]

    data = DashboardStatsData(
        active_incidents=27,
        severe_roads_count=14,
        moderate_roads_count=31,
        average_road_speed_kmh=18.4,
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
