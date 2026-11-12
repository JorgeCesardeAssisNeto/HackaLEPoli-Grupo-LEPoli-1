"""
Normalizador de payloads da ROOK API -> campos de WearableDailyMetric.

Os payloads da ROOK (webhook e REST) são aninhados por "pilar"
(sleep_health / physical_health / body_health) e os nomes de campo carregam sufixos de tipo
(ex.: steps_int, hr_resting_bpm_int). Para tolerar variações de versão do schema, a extração
é feita por busca recursiva de chaves, e não por caminhos fixos.
"""

import logging
import math
from datetime import date
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

logger = logging.getLogger(__name__)

# Tipos de "data_structure" que consolidam métricas diárias
SUMMARY_STRUCTURES = {"sleep_summary", "physical_summary", "body_summary"}


def compute_icd(avg_hr_day_bpm: Optional[float], steps: Optional[int]) -> Optional[float]:
    """ICD = HR_day / ln(steps + 1), com passos mínimos = 1 para evitar divisão por zero."""
    if avg_hr_day_bpm is None or steps is None:
        return None
    try:
        return round(float(avg_hr_day_bpm) / math.log(max(int(steps), 1) + 1.0), 2)
    except Exception as exc:
        logger.warning("Falha ao calcular ICD: %s", exc)
        return None


def _walk(obj: Any) -> Iterator[Tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key, value
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _find_number(payload: Any, predicate: Callable[[str], bool]) -> Optional[float]:
    for key, value in _walk(payload):
        if (
            predicate(key.lower())
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            return float(value)
    return None


def _find_date(payload: Any) -> Optional[date]:
    wanted = ("datetime_string", "date_string", "date", "start_datetime", "datetime")
    for key, value in _walk(payload):
        if key.lower() in wanted and isinstance(value, str) and len(value) >= 10:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                continue
    return None


def normalize_rook_payload(
    patient_id: str,
    payload: Dict[str, Any],
    default_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Converte um payload ROOK (webhook ou REST) em um dicionário parcial de campos
    de wearable_daily_metrics. Apenas campos encontrados são retornados; o upsert
    mescla com o que já existe no banco (summaries chegam em eventos separados).
    """
    fields: Dict[str, Any] = {
        "patient_id": patient_id,
        "date": _find_date(payload) or default_date or date.today(),
        "raw_payload": payload,
    }

    def put(name: str, value: Optional[float], cast=float) -> None:
        if value is not None:
            fields[name] = cast(value)

    # Atividade (Camada 1)
    put("steps", _find_number(payload, lambda k: k.startswith("steps")), int)
    put("distance_meters", _find_number(payload, lambda k: k.startswith("distance") and "meter" in k))
    put("active_calories_kcal", _find_number(payload, lambda k: "calories" in k and "active" in k))

    # Cardiovascular / autonômico (Camada 2)
    put("resting_hr_bpm", _find_number(payload, lambda k: "hr_resting" in k or "resting_hr" in k))
    put("avg_hr_day_bpm", _find_number(payload, lambda k: "hr_avg" in k or "avg_hr" in k))
    hrv = _find_number(payload, lambda k: "hrv" in k and "rmssd" in k and "avg" in k)
    if hrv is None:
        hrv = _find_number(payload, lambda k: "hrv" in k and "rmssd" in k)
    put("hrv_rmssd_ms", hrv)
    put("spo2_avg_pct", _find_number(payload, lambda k: "spo2" in k and "avg" in k))

    # Sono (Camada 2)
    total_s = _find_number(payload, lambda k: k.startswith("sleep_duration_seconds"))
    if total_s:
        put("sleep_duration_hours", round(total_s / 3600.0, 2))
        for needle, column in (
            ("deep_sleep_duration_seconds", "sleep_stage_deep_pct"),
            ("rem_sleep_duration_seconds", "sleep_stage_rem_pct"),
            ("light_sleep_duration_seconds", "sleep_stage_light_pct"),
        ):
            stage = _find_number(payload, lambda k, n=needle: n in k)
            if stage is not None:
                put(column, round(stage / total_s, 3))
    awake_s = _find_number(payload, lambda k: "awake_during_sleep" in k)
    put("waso_min", round(awake_s / 60.0, 1) if awake_s is not None else None)
    latency_s = _find_number(payload, lambda k: "time_to_fall_asleep" in k)
    put("sleep_latency_min", round(latency_s / 60.0, 1) if latency_s is not None else None)
    efficiency = _find_number(payload, lambda k: k.startswith("sleep_efficiency"))
    if efficiency is not None:
        put("sleep_efficiency", efficiency / 100.0 if efficiency > 1 else efficiency)

    return fields

