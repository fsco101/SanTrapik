from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from backend.app.schemas.coordinates import Coordinate

class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    include_alternatives: bool = Field(False, description="Whether to compute alternative routes")

class IncidentSummary(BaseModel):
    id: str
    type: str
    severity: str
    description: Optional[str] = None
    reported_at: str
    status: str

class SegmentPrediction(BaseModel):
    predicted_relief_time: str
    predicted_relief_minutes: int
    confidence: float

class RouteSegmentDetail(BaseModel):
    segment_id: str
    name: str
    road_code: Optional[str] = None
    direction: str
    traffic_level: str  # 'NORMAL', 'MODERATE', 'HEAVY', 'SEVERE'
    average_speed_kmh: float
    congestion_percentage: float
    incidents: List[IncidentSummary] = []
    prediction: Optional[SegmentPrediction] = None
    last_updated: str

class RouteSummary(BaseModel):
    total_distance_km: float
    estimated_travel_time_min: int
    normal_travel_time_min: int
    estimated_delay_min: int
    overall_congestion: str
    active_incidents_count: int
    most_affected_segment: str

class ExpectedRelief(BaseModel):
    relief_time: str
    estimated_minutes_remaining: int
    confidence: float
    confidence_interval: Optional[str] = None
    is_predicted: bool = True
    model_version: Optional[str] = "v1.4-rt-gbr"

class GeoJSONLineString(BaseModel):
    type: str = "LineString"
    coordinates: List[List[float]]

class RouteItem(BaseModel):
    id: str
    name: str
    is_recommended: bool = True
    recommendation_reason: Optional[str] = None
    summary: RouteSummary
    expected_relief: ExpectedRelief
    geometry: GeoJSONLineString
    segments: List[RouteSegmentDetail]

class RouteAnalyzeData(BaseModel):
    routes: List[RouteItem]

class RouteAnalyzeResponse(BaseModel):
    status: str = "success"
    data: RouteAnalyzeData
    meta: Dict[str, Any]
