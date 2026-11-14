from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class MappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    rook_user_id: str
    data_source: Optional[str] = None
    is_active: bool
    created_at: datetime

class DailyMetricCreate(BaseModel):
    patient_id: str
    date: date
    steps: Optional[int] = None
    distance_meters: Optional[float] = None
    active_calories_kcal: Optional[float] = None
    workout_minutes: Optional[float] = None
    resting_hr_bpm: Optional[float] = None
    avg_hr_day_bpm: Optional[float] = None
    hrv_rmssd_ms: Optional[float] = None
    spo2_avg_pct: Optional[float] = None
    sbp_mmHg: Optional[float] = None
    dbp_mmHg: Optional[float] = None
    sleep_duration_hours: Optional[float] = None
    sleep_efficiency: Optional[float] = None
    sleep_latency_min: Optional[float] = None
    waso_min: Optional[float] = None
    sleep_stage_deep_pct: Optional[float] = None
    sleep_stage_rem_pct: Optional[float] = None
    sleep_stage_light_pct: Optional[float] = None
    screen_time_min: Optional[float] = None
    caffeine_mg: Optional[float] = None
    alcohol_units: Optional[float] = None
    stress_score: Optional[float] = None
    raw_payload: Optional[Dict[str, Any]] = None

class DailyMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    date: date
    steps: Optional[int] = None
    resting_hr_bpm: Optional[float] = None
    avg_hr_day_bpm: Optional[float] = None
    hrv_rmssd_ms: Optional[float] = None
    sleep_duration_hours: Optional[float] = None
    sleep_stage_deep_pct: Optional[float] = None
    waso_min: Optional[float] = None
    screen_time_min: Optional[float] = None
    caffeine_mg: Optional[float] = None
    alcohol_units: Optional[float] = None
    icd_index: Optional[float] = None
    created_at: datetime

