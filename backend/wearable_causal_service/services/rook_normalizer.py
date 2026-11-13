"""
Normalizador de payloads ROOK -> campos de WearableDailyMetric.

Aceita dois formatos:
  a) ROOK v2 aninhado (sleep_health.summary.sleep_summary, physical_health.summary.physical_summary,
     body_health.summary.body_summary, ou arrays/dicts em "data");
  b) JSON plano/simplificado de sandbox (steps, resting_heart_rate, hrv, sleep_duration, caffeine_mg...).

Os payloads são "achatados" (primeira ocorrência de cada chave, em qualquer profundidade) e os campos
são resolvidos por uma lista de nomes exatos em ordem de prioridade, com fallback fuzzy.
Apenas campos presentes são retornados, para permitir o merge não destrutivo no upsert.
"""

import logging
import math
from datetime import date
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

SUMMARY_STRUCTURES = {"sleep_summary", "physical_summary", "body_summary"}

DEFAULT_PATIENT_ID = "e4a7a8d2-1b1e-4c7b-8b9a-112233445566"

# Colunas de métricas (exclui patient_id, date, raw_payload, icd_index)
METRIC_FIELDS = (
    "steps", "distance_meters", "active_calories_kcal", "workout_minutes",
    "resting_hr_bpm", "avg_hr_day_bpm", "hrv_rmssd_ms", "spo2_avg_pct",
    "sleep_duration_hours", "sleep_efficiency", "sleep_latency_min", "waso_min",
    "sleep_stage_deep_pct", "sleep_stage_rem_pct", "sleep_stage_light_pct",
    "screen_time_min", "caffeine_mg", "alcohol_units", "stress_score",
)


def compute_icd(avg_hr_day_bpm: Optional[float], steps: Optional[int]) -> Optional[float]:
    """ICD = HR_day / ln(max(steps, 1) + 1)."""
    if avg_hr_day_bpm is None or steps is None:
        return None
    try:
        return round(float(avg_hr_day_bpm) / math.log(max(int(steps), 1) + 1.0), 2)
    except Exception as exc:
        logger.warning("Falha ao calcular ICD: %s", exc)
        return None


# ----------------------------------------------------------------------------- helpers
def _walk(obj: Any) -> Iterator[Tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                yield from _walk(value)
            else:
                yield str(key).lower(), value
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _flatten(payload: Any) -> Dict[str, Any]:
    """Primeira ocorrência de cada chave escalar (minúscula), em qualquer profundidade."""
    flat: Dict[str, Any] = {}
    for key, value in _walk(payload):
        if value is not None and key not in flat:
            flat[key] = value
    return flat


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _pick(
    flat: Dict[str, Any],
    exact: Tuple[str, ...],
    fuzzy: Optional[Callable[[str], bool]] = None,
) -> Optional[Tuple[str, float]]:
    """Retorna (chave, valor) pelo primeiro nome exato disponível; senão pelo fallback fuzzy."""
    for name in exact:
        number = _as_number(flat.get(name))
        if number is not None:
            return name, number
    if fuzzy:
        for key, value in flat.items():
            number = _as_number(value)
            if number is not None and fuzzy(key):
                return key, number
    return None


def _num(flat, exact, fuzzy=None) -> Optional[float]:
    hit = _pick(flat, exact, fuzzy)
    return hit[1] if hit else None


def _find_date(flat: Dict[str, Any]) -> Optional[date]:
    for key in ("date", "summary_date", "datetime_string", "date_string", "start_datetime", "datetime"):
        value = flat.get(key)
        if isinstance(value, str) and len(value) >= 10:
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                continue
    return None


def extract_user_id(payload: Dict[str, Any]) -> str:
    """user_id | user.user_id | client_uuid | id de fallback — o webhook nunca deve falhar por isso."""
    user = payload.get("user")
    candidates = [
        payload.get("user_id"),
        user.get("user_id") if isinstance(user, dict) else None,
        payload.get("client_uuid"),
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    return DEFAULT_PATIENT_ID


def extract_records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Divide payloads com múltiplos itens em "data" (lista) em registros independentes."""
    data = payload.get("data")
    items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
    items = [i for i in items if isinstance(i, dict)]
    if not items:
        return [payload]
    records = []
    for item in items:
        record = dict(item)
        for key in ("data_structure", "user_id", "client_uuid", "user"):
            if key in payload:
                record.setdefault(key, payload[key])
        records.append(record)
    return records


def has_metrics(fields: Dict[str, Any]) -> bool:
    return any(fields.get(name) is not None for name in METRIC_FIELDS)


# ----------------------------------------------------------------------------- normalizer
def normalize_rook_payload(
    patient_id: str,
    payload: Dict[str, Any],
    default_date: Optional[date] = None,
) -> Dict[str, Any]:
    flat = _flatten(payload)
    fields: Dict[str, Any] = {
        "patient_id": patient_id,
        "date": _find_date(flat) or default_date or date.today(),
        "raw_payload": payload,
    }

    def put(name: str, value: Optional[float], cast=float) -> None:
        if value is not None:
            fields[name] = cast(value)

    # ---- Físico (Camada 1)
    put("steps", _num(flat, ("steps_int", "steps", "steps_count"),
                      lambda k: k.startswith("steps") and "goal" not in k), int)
    put("distance_meters", _num(flat, ("traveled_distance_meters_float", "traveled_distance_meters_int",
                                       "distance_walked", "distance_meters", "walked_distance_meters_float")))
    put("active_calories_kcal", _num(flat, ("active_calories_kcal_float", "active_calories_kcal_int",
                                            "calories_active", "active_calories_kcal")))

    # workout_minutes = moderado + vigoroso (segundos ou minutos, conforme o nome da chave)
    workout = 0.0
    found_workout = False
    for level in ("moderate", "vigorous"):
        hit = _pick(flat, (), lambda k, lv=level: lv in k and ("duration" in k or "minutes" in k or "seconds" in k)
                    and "heart" not in k)
        if hit:
            found_workout = True
            workout += hit[1] / 60.0 if "second" in hit[0] else hit[1]
    if found_workout:
        fields["workout_minutes"] = round(workout, 1)
    elif _num(flat, ("workout_minutes",)) is not None:
        fields["workout_minutes"] = _num(flat, ("workout_minutes",))

    # ---- Cardiovascular / autonômico (Camada 2)
    put("resting_hr_bpm", _num(flat, ("hr_resting_bpm_int", "hr_resting_bpm_float", "resting_hr_bpm",
                                      "resting_heart_rate"), lambda k: "hr_resting" in k))
    put("avg_hr_day_bpm", _num(flat, ("hr_avg_bpm_int", "hr_avg_bpm_float", "avg_hr_day_bpm",
                                      "average_heart_rate"), lambda k: "hr_avg" in k))
    put("hrv_rmssd_ms", _num(flat, ("hrv_avg_rmssd_float", "hrv_avg_rmssd_int", "hrv_rmssd_ms", "hrv"),
                             lambda k: "hrv" in k and "rmssd" in k and "max" not in k and "min" not in k))
    put("spo2_avg_pct", _num(flat, ("saturation_avg_percentage_int", "saturation_avg_percentage_float",
                                    "spo2_avg_pct")))

    # ---- Sono
    total_hit = _pick(flat, ("sleep_duration_seconds_int", "sleep_duration_seconds", "sleep_duration"))
    total_s = total_hit[1] if total_hit else None
    hours = _num(flat, ("sleep_duration_hours",))
    if total_s is not None:
        put("sleep_duration_hours", round(total_s / 3600.0, 2))
    elif hours is not None:
        put("sleep_duration_hours", hours)
        total_s = hours * 3600.0

    for column, names in (
        ("sleep_stage_deep_pct", ("deep_sleep_duration_seconds_int", "deep_sleep_duration_seconds", "deep_sleep_duration")),
        ("sleep_stage_rem_pct", ("rem_sleep_duration_seconds_int", "rem_sleep_duration_seconds", "rem_sleep_duration")),
        ("sleep_stage_light_pct", ("light_sleep_duration_seconds_int", "light_sleep_duration_seconds", "light_sleep_duration")),
    ):
        stage = _num(flat, names)
        if stage is not None and total_s:
            put(column, round(stage / total_s, 3))
        else:
            ready = _num(flat, (column,))  # fração pronta em payloads planos
            if ready is not None:
                put(column, ready / 100.0 if ready > 1 else ready)

    awake_s = _num(flat, ("time_awake_during_sleep_seconds_int", "time_awake_during_sleep_seconds"))
    if awake_s is not None:
        put("waso_min", round(awake_s / 60.0, 1))
    else:
        put("waso_min", _num(flat, ("waso_min",)))

    latency_s = _num(flat, ("time_to_fall_asleep_seconds_int", "time_to_fall_asleep_seconds"))
    if latency_s is not None:
        put("sleep_latency_min", round(latency_s / 60.0, 1))
    else:
        put("sleep_latency_min", _num(flat, ("sleep_latency_min",)))

    efficiency = _num(flat, ("sleep_efficiency_1_100_score_int", "sleep_efficiency"))
    if efficiency is not None:
        put("sleep_efficiency", efficiency / 100.0 if efficiency > 1 else efficiency)

    # ---- Confundidores de estilo de vida / estresse (payloads planos)
    put("screen_time_min", _num(flat, ("screen_time_min",)))
    put("caffeine_mg", _num(flat, ("caffeine_mg",)))
    put("alcohol_units", _num(flat, ("alcohol_units",)))
    put("stress_score", _num(flat, ("stress_score",)))

    # ICD parcial (o upsert recalcula após o merge com o registro existente)
    icd = compute_icd(fields.get("avg_hr_day_bpm"), fields.get("steps"))
    if icd is not None:
        fields["icd_index"] = icd

    return fields
