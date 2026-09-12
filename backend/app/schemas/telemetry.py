from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: Dict[str, Any]
    geometry: Dict[str, Any]

class TrafficHeatmapResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class IncidentItem(BaseModel):
    id: str
    incident_type: str
    description: Optional[str] = None
    severity: str
    status: str
    lat: float
    lng: float
    reported_at: str
    cleared_at: Optional[str] = None
    data_source: str
    road_segment_id: Optional[str] = None
    corridor: Optional[str] = None

class IncidentListResponse(BaseModel):
    status: str = "success"
    data: List[IncidentItem]
    meta: Dict[str, Any]

class CorridorCongestion(BaseModel):
    road_name: str
    traffic_level: str
    congestion_percentage: float
    average_speed_kmh: float
    expected_relief: str

class DashboardStatsData(BaseModel):
    active_incidents: int
    severe_roads_count: int
    moderate_roads_count: int
    average_road_speed_kmh: float
    most_congested_roads: List[CorridorCongestion]

class DashboardStatsResponse(BaseModel):
    status: str = "success"
    data: DashboardStatsData
    meta: Dict[str, Any]
