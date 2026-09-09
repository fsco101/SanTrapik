from pydantic import BaseModel, Field, field_validator
from typing import Optional
from backend.app.core.config import settings

class Coordinate(BaseModel):
    lat: float = Field(..., description="Latitude in WGS 84")
    lng: float = Field(..., description="Longitude in WGS 84")
    name: Optional[str] = Field(None, description="Human readable landmark name")

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        min_lng, min_lat, max_lng, max_lat = settings.METRO_MANILA_BBOX
        if not (min_lat <= v <= max_lat):
            raise ValueError(f"Latitude {v} is outside Metro Manila bounds [{min_lat}, {max_lat}]")
        return v

    @field_validator("lng")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        min_lng, min_lat, max_lng, max_lat = settings.METRO_MANILA_BBOX
        if not (min_lng <= v <= max_lng):
            raise ValueError(f"Longitude {v} is outside Metro Manila bounds [{min_lng}, {max_lng}]")
        return v
