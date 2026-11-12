import logging
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from database import get_db
from models.wearable_metrics import WearableDailyMetric
from models.causal_results import CausalEvaluation, ClinicalAlert
from schemas.causal import (
    CausalEvaluationResponse,
    ClinicalAlertResponse,
    TargetEvaluationResult
)
from services.causal_engine import causal_engine
from services.alert_service import alert_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/causal", tags=["3-Layer Causal Inference Engine"])

@router.post(
    "/evaluate/{patient_id}",
    response_model=CausalEvaluationResponse,
    summary="Evaluate Causal DAG for Patient Trailing Window"
)
async def evaluate_patient_causal(
    patient_id: str,
    days: int = Query(14, ge=1, le=90, description="Trailing history window in days"),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes the 3-Layer Causal Inference DAG across the 4 Clinical Targets:
      1. Deep Sleep N3 Deficiency (< 16%) vs Step Volume (< 6,500) & Alcohol / WASO
      2. Metabolic Risk (Resting HR >= 72 bpm) vs Screen Time (> 130 min) & Caffeine (> 80 mg)
      3. Systemic Inflammation (HRV < 38 ms) vs Sleep Debt (< 6h) & Alcohol (4-day rule)
      4. Anemia Screening (Daytime HR > 92 bpm with low steps, ICD formula) cross-referenced with FHIR Lab
    """
    # Fetch historical records
    stmt = select(WearableDailyMetric).where(
        WearableDailyMetric.patient_id == patient_id
    ).order_by(WearableDailyMetric.date.asc())

    records = (await db.execute(stmt)).scalars().all()
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No wearable metrics recorded for patient_id={patient_id}."
        )

    # Convert to dictionaries
    dict_records = [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in records
    ]
    latest_metric = dict_records[-1]
    latest_db_record = records[-1]

    # Evaluate all targets
    target_results: List[TargetEvaluationResult] = await causal_engine.evaluate_all_targets(
        patient_id=patient_id,
        current_metric=latest_metric,
        historical_records=dict_records
    )

    # Persist evaluations and clinical alerts
    new_alerts = await alert_service.persist_evaluations_and_alerts(
        db, patient_id, latest_db_record.id, target_results
    )
    await db.commit()

    # Calculate statistics
    anomalies_detected = sum(1 for r in target_results if r.is_anomaly)
    mitigated_count = sum(1 for r in target_results if r.is_confounded)
    mitigation_rate = round((mitigated_count / anomalies_detected * 100.0), 1) if anomalies_detected > 0 else 100.0

    return CausalEvaluationResponse(
        patient_id=patient_id,
        evaluation_date=latest_metric["date"],
        days_analyzed=min(len(records), days),
        targets_evaluated=target_results,
        total_anomalies_detected=anomalies_detected,
        total_mitigated_by_confounders=mitigated_count,
        mitigation_rate_pct=mitigation_rate,
        clinical_alerts_generated=new_alerts
    )

@router.get(
    "/alerts/{patient_id}",
    response_model=List[ClinicalAlertResponse],
    summary="List Generated Clinical Alerts"
)
async def get_patient_alerts(
    patient_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by status: PENDING, NOTIFIED, DISMISSED"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves actionable clinical alerts triggered after passing through the causal filter."""
    stmt = select(ClinicalAlert).where(ClinicalAlert.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(ClinicalAlert.status == status_filter.upper())
    stmt = stmt.order_by(desc(ClinicalAlert.created_at))

    alerts = (await db.execute(stmt)).scalars().all()
    return alerts

@router.patch(
    "/alerts/{alert_id}",
    response_model=ClinicalAlertResponse,
    summary="Update Alert Status (Clinician Review)"
)
async def update_alert_status(
    alert_id: str,
    new_status: str = Query(..., pattern="^(PENDING|NOTIFIED|DISMISSED|RESOLVED)$"),
    db: AsyncSession = Depends(get_db)
):
    """Allows physicians to mark alerts as notified, dismissed, or resolved."""
    stmt = select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
    alert = (await db.execute(stmt)).scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.status = new_status
    await db.commit()
    await db.refresh(alert)
    return alert

