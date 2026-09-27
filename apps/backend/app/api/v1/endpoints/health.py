import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.vector import check_qdrant_health

router = APIRouter()

_START_TIME = time.time()


@router.get("/health", tags=["Health"])
async def liveness():
    """
    Basic liveness check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/health/readiness", tags=["Health"])
async def readiness(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive readiness check verifying database and vector store connectivity.
    """
    db_status = "unknown"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    vector_healthy = check_qdrant_health()
    vector_status = "connected" if vector_healthy else "unavailable"

    is_ready = db_status == "connected" and vector_healthy

    return {
        "status": "ready" if is_ready else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": db_status,
            "vector_store": vector_status,
        },
        "timestamp": time.time()
    }
