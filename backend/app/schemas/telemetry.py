from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Any, Dict, Literal
from backend.app.core.spatial_guardrails import validate_philippine_coordinate, sanitize_text_input

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: Dict[str, Any]
    geometry: Dict[str, Any]

class TrafficHeatmapResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class IncidentCreateRequest(BaseModel):
    incident_type: str = Field(..., description="Type of incident: ACCIDENT, ROADWORK, FLOOD, STALLED_VEHICLE, HAZARD, OTHER")
    severity: str = Field(default="MEDIUM", description="Severity tier: LOW, MEDIUM, HIGH, CRITICAL")
    lat: Optional[float] = Field(default=None, description="Latitude coordinate in Metro Manila (14.35 to 14.80)")
    lng: Optional[float] = Field(default=None, description="Longitude coordinate in Metro Manila (120.90 to 121.15)")
    point_lng_lat: Optional[List[float]] = Field(default=None, description="[lng, lat] GeoJSON coordinate pair")
    description: str = Field(default="Reported traffic obstruction", description="Commuter description, max 280 characters")
    corridor: Optional[str] = Field(default=None, description="Corridor name hint e.g. EDSA, C-5")
    status: Optional[str] = Field(default=None, description="Incident status")
    data_source: Optional[str] = Field(default="COMMUTER_REPORT", description="Origin source attribution")

    @model_validator(mode="before")
    @classmethod
    def extract_and_validate_coords(cls, data: Any) -> Any:
        if isinstance(data, dict):
            point = data.get("point_lng_lat")
            if point and len(point) >= 2:
                if data.get("lng") is None:
                    data["lng"] = float(point[0])
                if data.get("lat") is None:
                    data["lat"] = float(point[1])
            
            # Check coordinates exist
            lat = data.get("lat")
            lng = data.get("lng")
            if lat is None or lng is None:
                raise ValueError("Both 'lat' and 'lng' (or 'point_lng_lat') coordinates are required.")
            
            if not (14.35 <= float(lat) <= 14.80):
                raise ValueError(f"Latitude {lat} is outside Metro Manila boundaries (14.35 to 14.80)")
            if not (120.90 <= float(lng) <= 121.15):
                raise ValueError(f"Longitude {lng} is outside Metro Manila boundaries (120.90 to 121.15)")
        return data

    @field_validator("incident_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"ACCIDENT", "ROADWORK", "FLOOD", "STALLED_VEHICLE", "HAZARD", "OTHER"}
        upper_v = v.strip().upper()
        if upper_v not in valid_types:
            raise ValueError(f"Invalid incident type '{v}'. Allowed types: {sorted(valid_types)}")
        return upper_v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid_sevs = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        upper_v = v.strip().upper()
        if upper_v not in valid_sevs:
            raise ValueError(f"Invalid severity '{v}'. Allowed tiers: {sorted(valid_sevs)}")
        return upper_v

    @field_validator("description")
    @classmethod
    def sanitize_desc(cls, v: str) -> str:
        return sanitize_text_input(v, max_length=280)

class IncidentClearanceVoteRequest(BaseModel):
    vote: Literal["STILL_THERE", "CLEARED"] = Field(..., description="Community clearance verification vote")

class IncidentItem(BaseModel):
    id: str
    incident_type: str
    description: Optional[str] = None
    severity: str
    status: str
    lat: float
    lng: float
    point_lng_lat: Optional[List[float]] = None
    reported_at: str
    cleared_at: Optional[str] = None
    data_source: str
    road_segment_id: Optional[str] = None
    corridor: Optional[str] = None
    confidence: float = 0.85
    report_count: int = 1
    still_there_votes: int = 0
    cleared_votes: int = 0
    reporter_token: Optional[str] = None

class IncidentListResponse(BaseModel):
    status: str = "success"
    data: List[IncidentItem]
    meta: Dict[str, Any]

class IncidentCreateResponse(BaseModel):
    status: str = "success"
    message: str
    data: IncidentItem

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
