from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional, Union

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SanTrapik"
    API_V1_STR: str = "/api/v1"
    
    # Server host & port
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # PostgreSQL / PostGIS connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "santrapik"
    
    DATABASE_URL: Optional[str] = None
    ASYNC_DATABASE_URL: Optional[str] = None
    
    # CORS Origins (list or comma-separated string)
    CORS_ORIGINS: Union[list[str], str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]
    
    # Metro Manila Bounding Box: [min_lng, min_lat, max_lng, max_lat]
    METRO_MANILA_BBOX: Union[tuple, list, str] = (120.90, 14.35, 121.15, 14.80)
    
    # External Routing Engine URL
    OSRM_URL: str = "https://router.project-osrm.org"
    
    model_config = {
        "env_file": (str(BACKEND_DIR / ".env"), ".env"),
        "case_sensitive": True,
        "extra": "ignore"
    }

    @field_validator("METRO_MANILA_BBOX")
    @classmethod
    def validate_bbox(cls, v) -> tuple:
        if isinstance(v, str):
            clean = v.strip("[]() ")
            return tuple(float(x.strip()) for x in clean.split(",") if x.strip())
        if isinstance(v, (list, tuple)):
            return tuple(float(x) for x in v)
        return (120.90, 14.35, 121.15, 14.80)

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors(cls, v) -> list[str]:
        if isinstance(v, str):
            clean = v.strip("[] ")
            return [o.strip().strip("'\"") for o in clean.split(",") if o.strip()]
        return list(v)
    
    def get_metro_manila_bbox(self) -> tuple:
        return self.METRO_MANILA_BBOX
    
    def get_cors_origins(self) -> list[str]:
        return self.CORS_ORIGINS
    
    def get_database_url(self) -> str:
        url = self.DATABASE_URL or f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        if url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    def get_async_database_url(self) -> str:
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
