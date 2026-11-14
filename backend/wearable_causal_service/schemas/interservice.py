from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, model_validator

_CLASSIFICACAO_CODIGO_MAP = {
    "NORMAL": "VERDE",
    "LIMITROFE": "AMARELO",
    "ALTERADO_LEVE": "AMARELO",
    "ALTERADO_MODERADO": "VERMELHO",
    "ALTERACAO_ACENTUADA": "VERMELHO",
}

_COR_NOME_MAP = {
    "verde": "VERDE",
    "amarelo": "AMARELO",
    "âmbar": "AMARELO",
    "ambar": "AMARELO",
    "laranja": "VERMELHO",
    "vermelho": "VERMELHO",
}


class FHIRPatientInfo(BaseModel):
    id: str
    nome: Optional[str] = None
    sexo: Optional[str] = None
    sexo_biologico: Optional[str] = None
    idade: Optional[int] = None

    @model_validator(mode="after")
    def _normalize_sexo(self):
        if self.sexo is None and self.sexo_biologico is not None:
            self.sexo = self.sexo_biologico
        return self


class FHIRObservationPoint(BaseModel):
    data_coleta: Optional[str] = None
    data_coleta_iso: Optional[str] = None
    valor_numerico: Optional[float] = None
    status_classificacao: Optional[str] = None  # 'VERDE', 'AMARELO', 'VERMELHO'
    classificacao: Optional[Dict[str, Any]] = None
    tendencia: Optional[Union[str, Dict[str, Any]]] = None

    @model_validator(mode="after")
    def _normalize_observation(self):
        if self.data_coleta is None and self.data_coleta_iso is not None:
            self.data_coleta = self.data_coleta_iso
        if self.status_classificacao is None and isinstance(self.classificacao, dict):
            codigo = str(self.classificacao.get("codigo_4") or self.classificacao.get("codigo") or "").upper()
            cor = str(self.classificacao.get("cor_nome_4") or self.classificacao.get("cor_nome") or "").strip().lower()
            self.status_classificacao = _CLASSIFICACAO_CODIGO_MAP.get(codigo) or _COR_NOME_MAP.get(cor)
        return self


class FHIRLabEvolutionResponse(BaseModel):
    paciente: Optional[FHIRPatientInfo] = None
    codigo_loinc: str
    nome_analito: Optional[str] = None
    nome_exame: Optional[str] = None
    unidade: Optional[str] = None
    faixa_referencia: Optional[Dict[str, Optional[float]]] = None
    faixa_referencia_min: Optional[float] = None
    faixa_referencia_max: Optional[float] = None
    serie_temporal: List[FHIRObservationPoint] = []

    @model_validator(mode="after")
    def _normalize_fields(self):
        if self.nome_analito is None and self.nome_exame is not None:
            self.nome_analito = self.nome_exame
        if self.faixa_referencia is None and (
            self.faixa_referencia_min is not None or self.faixa_referencia_max is not None
        ):
            self.faixa_referencia = {
                "min": self.faixa_referencia_min,
                "max": self.faixa_referencia_max,
            }
        return self


class NHANESBaselineMetrics(BaseModel):
    expected_resting_hr_bpm: Optional[float] = None
    delta_individual_bpm: Optional[float] = None
    calibrated_r2: Optional[float] = None


class NHANESBaselineResponse(BaseModel):
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    baseline_metrics: Optional[NHANESBaselineMetrics] = None
    risk_flags: Optional[Dict[str, Any]] = None
