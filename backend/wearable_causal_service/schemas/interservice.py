from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class FHIRPatientInfo(BaseModel):
    id: str
    nome: Optional[str] = None
    sexo: Optional[str] = None
    idade: Optional[int] = None

class FHIRObservationPoint(BaseModel):
    data_coleta: Optional[str] = None
    valor_numerico: Optional[float] = None
    status_classificacao: Optional[str] = None  # 'VERDE', 'AMARELO', 'VERMELHO'
    tendencia: Optional[str] = None

class FHIRLabEvolutionResponse(BaseModel):
    paciente: Optional[FHIRPatientInfo] = None
    codigo_loinc: str
    nome_analito: Optional[str] = None
    unidade: Optional[str] = None
    faixa_referencia: Optional[Dict[str, Optional[float]]] = None
    serie_temporal: List[FHIRObservationPoint] = []

class NHANESBaselineMetrics(BaseModel):
    expected_resting_hr_bpm: Optional[float] = None
    delta_individual_bpm: Optional[float] = None
    calibrated_r2: Optional[float] = None

class NHANESBaselineResponse(BaseModel):
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    baseline_metrics: Optional[NHANESBaselineMetrics] = None
    risk_flags: Optional[Dict[str, Any]] = None

