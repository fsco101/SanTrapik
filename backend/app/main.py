import os
import sys

# Ensure repository root is in sys.path so 'backend' is always resolvable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.services.decay_worker import decay_worker
from backend.app.services.telemetry import telemetry_service

from backend.app.services.streaming import stream_manager

async def periodic_telemetry_broadcaster():
    """Periodically streams velocity deltas and macro stats to active SSE subscribers."""
    while True:
        try:
            await asyncio.sleep(20)
            if stream_manager.active_subscriber_count > 0:
                deltas = telemetry_service.get_live_velocity_deltas()
                await stream_manager.broadcast_velocity_deltas(deltas)
                stats = telemetry_service.get_live_dashboard_stats()
                await stream_manager.broadcast_stats(stats)
        except asyncio.CancelledError:
            break
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start incident decay worker in background
    decay_task = asyncio.create_task(decay_worker.start(lambda: telemetry_service._live_incidents))
    broadcast_task = asyncio.create_task(periodic_telemetry_broadcaster())
    yield
    # Clean shutdown
    decay_worker.stop()
    decay_task.cancel()
    broadcast_task.cancel()
    try:
        await decay_task
    except asyncio.CancelledError:
        pass
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="SanTrapik API Gateway",
    description="AI-Powered Metro Manila Traffic Intelligence & Road Incident Monitoring System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*"
]

from backend.app.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, max_requests_per_minute=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins() or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to SanTrapik Traffic Intelligence API",
        "docs": "/docs",
        "version": "1.0.0",
        "focus": "Metro Manila, Philippines"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
