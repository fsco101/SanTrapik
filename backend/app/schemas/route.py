from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Literal
from backend.app.schemas.coordinates import Coordinate

class TollCostBenefit(BaseModel):
    toll_fee_php: float = 0.0
    time_saved_min: int = 0
    cost_per_min_saved: Optional[float] = None
    comparison_route_name: Optional[str] = None
    is_zero_toll: bool = True

class DelayDecomposition(BaseModel):
    incident_delay_min: float = 0.0
    baseline_congestion_min: float = 0.0
    weather_delay_min: float = 0.0
    total_delay_min: float = 0.0
    primary_cause: str = "NORMAL_FLOW"  # 'INCIDENT', 'RUSH_HOUR_VOLUME', 'MONSOON_FLOOD', 'NORMAL_FLOW'
    cause_details: str = ""

class NumberCodingAdvisory(BaseModel):
    is_coding_active: bool = False
    is_restricted: bool = False
    plate_ending: Optional[int] = None
    restricted_hours: str = "N/A"
    restricted_day: str = "None"
    has_window_hours: bool = True
    window_hours: str = ""
    message: str = ""
    affected_corridors: List[str] = []

class FloodHazardDetail(BaseModel):
    id: str
    corridor: str
    city: str
    water_depth: str  # 'GUTTER_DEEP', 'HALF_TIRE', 'TIRE_DEEP', 'SUBMERGED'
    passable_to_light: bool = True
    description: Optional[str] = None
    distance_meters: Optional[float] = None

class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    include_alternatives: bool = Field(False, description="Whether to compute alternative routes")
    transport_mode: Literal["car", "motorcycle", "jeepney", "walking"] = Field("car", description="Commute mode: car, motorcycle, jeepney, walking")
    use_expressway: bool = Field(True, description="Whether to utilize expressways / tollways (e.g. Skyway)")
    plate_ending: Optional[int] = Field(None, ge=0, le=9, description="Vehicle license plate ending digit (0-9)")

class IncidentSummary(BaseModel):
    id: str
    type: str
    severity: str
    description: Optional[str] = None
    reported_at: str
    status: str
    clearance_minutes: Optional[int] = None
    p10_clearance_mins: Optional[int] = None
    p50_clearance_mins: Optional[int] = None
    p90_clearance_mins: Optional[int] = None
    clearance_window_display: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_tier: Optional[str] = None
    tow_dispatch_status: Optional[str] = None
    lanes_blocked: Optional[int] = None
    road_width_lanes: Optional[int] = None

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
    p10_optimistic_mins: Optional[int] = None
    p50_median_mins: Optional[int] = None
    p90_pessimistic_mins: Optional[int] = None
    relief_window_display: Optional[str] = None
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
    badge: Optional[str] = None  # 'LEAST_TRAFFIC', 'SHORTEST_PATH', 'LEAST_TRAFFIC_AND_SHORTEST', 'ALTERNATIVE'
    distance_diff_km: Optional[float] = None
    time_diff_min: Optional[int] = None
    summary: RouteSummary
    expected_relief: ExpectedRelief
    geometry: GeoJSONLineString
    segments: List[RouteSegmentDetail]
    toll_fee_php: float = 0.0
    toll_cost_benefit: Optional[TollCostBenefit] = None
    delay_decomposition: Optional[DelayDecomposition] = None
    coding_advisory: Optional[NumberCodingAdvisory] = None
    flood_hazards: List[FloodHazardDetail] = []
    is_impassable_flood: bool = False
    spillover_warnings: List[str] = []
    spillover_segments: List[str] = []

class RouteAnalyzeData(BaseModel):
    routes: List[RouteItem]

class RouteAnalyzeResponse(BaseModel):
    status: str = "success"
    data: RouteAnalyzeData
    meta: Dict[str, Any]
