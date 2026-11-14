import logging
from datetime import timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.base import utc_now_naive
from models.causal_results import CausalEvaluation, ClinicalAlert
from schemas.causal import TargetEvaluationResult, ClinicalAlertResponse

logger = logging.getLogger(__name__)

class AlertService:
    """
    Manages the lifecycle and persistence of causal evaluation audit records
    and clinical alerts in the open_health.db relational database.
    """

    async def persist_evaluations_and_alerts(
        self,
        session: AsyncSession,
        patient_id: str,
        metric_id: str,
        evaluations: List[TargetEvaluationResult]
    ) -> List[ClinicalAlertResponse]:
        generated_alerts: List[ClinicalAlertResponse] = []

        for result in evaluations:
            # 1. Save CausalEvaluation audit log
            eval_record = CausalEvaluation(
                metric_id=metric_id,
                target_id=result.target_id,
                is_anomaly=result.is_anomaly,
                is_confounded=result.is_confounded,
                confounders_detected=result.confounders_detected,
                mitigation_verdict=result.mitigation_verdict,
                protocol_applied=result.protocol_applied,
                clinical_verdict=result.clinical_verdict,
                confidence_score=1.0
            )
            session.add(eval_record)
            await session.flush()  # Generate eval_record.id

            # 2. Check if a ClinicalAlert needs to be emitted
            if result.trigger_alert:
                # Anti-Fatigue Debounce: Check if an alert was emitted for this target in last 7 days
                seven_days_ago = utc_now_naive() - timedelta(days=7)
                stmt = select(ClinicalAlert).where(
                    and_(
                        ClinicalAlert.patient_id == patient_id,
                        ClinicalAlert.target_id == result.target_id,
                        ClinicalAlert.status.in_(["PENDING", "NOTIFIED"]),
                        ClinicalAlert.created_at >= seven_days_ago
                    )
                )
                existing = (await session.execute(stmt)).scalars().first()
                if existing:
                    logger.info(
                        "Clinical alert for %s on patient %s suppressed by 7-day debounce.",
                        result.target_id, patient_id
                    )
                    continue

                # Create fresh ClinicalAlert
                alert_record = ClinicalAlert(
                    patient_id=patient_id,
                    evaluation_id=eval_record.id,
                    target_id=result.target_id,
                    alert_level=result.alert_level or "WARNING",
                    recommended_loinc=result.recommended_loinc,
                    clinical_rationale=result.clinical_verdict,
                    recommended_action=result.protocol_applied,
                    status="PENDING"
                )
                session.add(alert_record)
                await session.flush()

                generated_alerts.append(ClinicalAlertResponse.model_validate(alert_record))

        return generated_alerts

# Singleton alert service instance
alert_service = AlertService()

