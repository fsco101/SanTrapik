from fastapi import APIRouter
from datetime import datetime, timezone
from backend.app.services.drift_monitor import drift_monitor

router = APIRouter()

@router.get("/health", summary="Health Check")
async def health_check():
    ml_health = drift_monitor.get_status()
    return {
        "status": "healthy" if ml_health["status"] != "FALLBACK" else "degraded",
        "service": "SanTrapik API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ml_inference": ml_health
    }

@router.get("/ml/status", summary="ML Model Inference & Circuit Breaker Status")
async def ml_status():
    """Reports active model inference state (OPERATIONAL, DEGRADED, FALLBACK) (SP9-004)."""
    return drift_monitor.get_status()
