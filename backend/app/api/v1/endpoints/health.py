from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health", summary="Health Check")
async def health_check():
    return {
        "status": "healthy",
        "service": "SanTrapik API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
