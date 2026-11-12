import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from models.base import Base

class CausalEvaluation(Base):
    """
    Detailed audit log for every execution of the 3-Layer Causal Inference DAG.
    Maintains scientific explainability on why an alert was triggered or mitigated.
    """
    __tablename__ = "causal_evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_id = Column(String(36), ForeignKey("wearable_daily_metrics.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(50), nullable=False, index=True)  
    # 'TARGET_1_DEEP_SLEEP', 'TARGET_2_METABOLIC_RISK', 'TARGET_3_INFLAMMATION_HRV', 'TARGET_4_ANEMIA_LOAD'
    
    is_anomaly = Column(Boolean, nullable=False)
    is_confounded = Column(Boolean, nullable=False)
    confounders_detected = Column(JSON, nullable=True)  # List[str], e.g. ["STEPS_BELOW_6500", "ALCOHOL_WASO"]
    mitigation_verdict = Column(String(50), nullable=False)  # 'MITIGATED', 'CLINICAL_ANOMALY', 'NORMAL'
    protocol_applied = Column(Text, nullable=False)
    clinical_verdict = Column(Text, nullable=False)
    
    persistence_days = Column(Integer, default=1, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    metric = relationship("WearableDailyMetric", back_populates="evaluations")
    alerts = relationship("ClinicalAlert", back_populates="evaluation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_causal_eval_metric_target", "metric_id", "target_id"),
        Index("idx_causal_eval_created", "created_at"),
    )

class ClinicalAlert(Base):
    """
    Actionable clinical alerts generated ONLY when physiological anomalies persist
    without being explained by Layer 1 lifestyle confounders.
    """
    __tablename__ = "clinical_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    evaluation_id = Column(String(36), ForeignKey("causal_evaluations.id", ondelete="SET NULL"), nullable=True)
    
    target_id = Column(String(50), nullable=False)
    alert_level = Column(String(20), nullable=False)  # 'INFO', 'WARNING', 'CRITICAL'
    recommended_loinc = Column(String(50), nullable=True)  # e.g., '2276-4' (Ferritin), '4548-4' (HbA1c)
    clinical_rationale = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    
    status = Column(String(20), default="PENDING", nullable=False)  # 'PENDING', 'NOTIFIED', 'DISMISSED'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    evaluation = relationship("CausalEvaluation", back_populates="alerts")

    __table_args__ = (
        Index("idx_clinical_alerts_patient_status", "patient_id", "status"),
        Index("idx_clinical_alerts_created", "created_at"),
    )

