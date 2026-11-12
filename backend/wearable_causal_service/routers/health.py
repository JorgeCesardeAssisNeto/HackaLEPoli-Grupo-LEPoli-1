import time
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from database import get_db
from models.wearable_metrics import WearableDailyMetric
from models.causal_results import ClinicalAlert
from config import settings

router = APIRouter(tags=["Health & Telemetry"])

START_TIME = time.time()

@router.get("/health", summary="Basic Health Check")
async def health_check():
    """Returns uptime, service name, and execution port."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "port": settings.PORT,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "database": settings.DATABASE_PATH
    }

@router.get("/health/ready", summary="Readiness Probe")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Validates that the database connection is live and responsive."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database_connected": True}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {exc}"
        )

@router.get("/metrics", summary="Operational Metrics")
async def operational_metrics(db: AsyncSession = Depends(get_db)):
    """Returns count of ingested wearable metrics and active clinical alerts."""
    try:
        total_metrics = (await db.execute(select(func.count(WearableDailyMetric.id)))).scalar_one()
        total_alerts = (await db.execute(select(func.count(ClinicalAlert.id)))).scalar_one()
        pending_alerts = (await db.execute(
            select(func.count(ClinicalAlert.id)).where(ClinicalAlert.status == "PENDING")
        )).scalar_one()

        return {
            "total_wearable_metrics_records": total_metrics,
            "total_clinical_alerts": total_alerts,
            "pending_clinical_alerts": pending_alerts,
            "timestamp": time.time()
        }
    except Exception as exc:
        return {"error": str(exc)}

