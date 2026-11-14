from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class TargetEvaluationResult(BaseModel):
    target_id: str
    title: str
    target_metric_description: str
    is_anomaly: bool
    is_confounded: bool
    confounders_detected: List[str] = Field(default_factory=list)
    mitigation_verdict: str  # 'NORMAL', 'MITIGATED', 'CLINICAL_ANOMALY'
    status_color: str  # '#34d399' (green/mitigated), '#fbbf24' (yellow), '#fb7185' (red)
    protocol_applied: str
    clinical_verdict: str
    trigger_alert: bool
    alert_level: Optional[str] = None  # 'INFO', 'WARNING', 'CRITICAL'
    recommended_loinc: Optional[str] = None

class ClinicalAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    target_id: str
    alert_level: str
    recommended_loinc: Optional[str] = None
    clinical_rationale: str
    recommended_action: str
    status: str
    created_at: datetime

class CausalEvaluationResponse(BaseModel):
    patient_id: str
    evaluation_date: date
    days_analyzed: int
    targets_evaluated: List[TargetEvaluationResult]
    total_anomalies_detected: int
    total_mitigated_by_confounders: int
    mitigation_rate_pct: float
    clinical_alerts_generated: List[ClinicalAlertResponse] = Field(default_factory=list)

class CausalEvaluationRequest(BaseModel):
    patient_id: str
    days: int = Field(default=14, ge=1, le=90, description="Rolling historical window in days")

