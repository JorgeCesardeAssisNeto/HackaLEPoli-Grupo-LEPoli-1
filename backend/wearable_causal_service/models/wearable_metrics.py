import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, 
    JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from models.base import Base

class WearableDailyMetric(Base):
    """
    Standardized daily physiological & lifestyle metrics aggregated from wearables.
    Stores Layer 1 (Lifestyle Confounders) and Layer 2 (Wearable Signals) data points.
    """
    __tablename__ = "wearable_daily_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    date = Column(Date, nullable=False)

    # Physical Activity
    steps = Column(Integer, nullable=True)
    distance_meters = Column(Float, nullable=True)
    active_calories_kcal = Column(Float, nullable=True)
    workout_minutes = Column(Float, nullable=True)

    # Cardiovascular & Autonomic Signals (Layer 2)
    resting_hr_bpm = Column(Float, nullable=True)
    avg_hr_day_bpm = Column(Float, nullable=True)
    hrv_rmssd_ms = Column(Float, nullable=True)
    spo2_avg_pct = Column(Float, nullable=True)
    sbp_mmHg = Column(Float, nullable=True)
    dbp_mmHg = Column(Float, nullable=True)

    # Sleep Architecture (Layer 2)
    sleep_duration_hours = Column(Float, nullable=True)
    sleep_efficiency = Column(Float, nullable=True)
    sleep_latency_min = Column(Float, nullable=True)
    waso_min = Column(Float, nullable=True)  # Wake After Sleep Onset
    sleep_stage_deep_pct = Column(Float, nullable=True)  # N3 Stage (0.00 to 1.00)
    sleep_stage_rem_pct = Column(Float, nullable=True)
    sleep_stage_light_pct = Column(Float, nullable=True)

    # Lifestyle & Exogenous Confounders (Layer 1)
    screen_time_min = Column(Float, nullable=True)
    caffeine_mg = Column(Float, nullable=True)
    alcohol_units = Column(Float, nullable=True)
    stress_score = Column(Float, nullable=True)

    # Derived Physiological Load Indices
    # ICD = HR_day / ln(steps + 1)
    icd_index = Column(Float, nullable=True)

    # Raw Payload & Metadata
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to Causal Inference Evaluations
    evaluations = relationship(
        "CausalEvaluation",
        back_populates="metric",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("patient_id", "date", name="uq_patient_daily_metric"),
        Index("idx_wearable_metrics_patient_date", "patient_id", "date"),
        Index("idx_wearable_metrics_date", "date"),
    )

