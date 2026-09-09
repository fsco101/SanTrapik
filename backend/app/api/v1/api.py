from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, route, traffic, incidents, dashboard

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(route.router, tags=["Route Intelligence"])
api_router.include_router(traffic.router, tags=["Traffic Telemetry"])
api_router.include_router(incidents.router, tags=["Road Incidents"])
api_router.include_router(dashboard.router, tags=["City Dashboard"])
