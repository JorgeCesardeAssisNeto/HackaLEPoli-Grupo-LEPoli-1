import math
from datetime import date
from services.rook_normalizer import (
    compute_icd, normalize_rook_payload, extract_user_id, extract_records, DEFAULT_PATIENT_ID,
)


def test_icd_formula():
    assert compute_icd(95.0, 2000) == round(95.0 / math.log(2001), 2)
    assert compute_icd(90.0, 0) == round(90.0 / math.log(2), 2)
    assert compute_icd(None, 100) is None


def test_nested_sleep_summary():
    payload = {"sleep_health": {"summary": {"sleep_summary": {
        "metadata": {"datetime_string": "2026-11-11T07:00:00Z"},
        "duration": {
            "sleep_duration_seconds_int": 25200,
            "deep_sleep_duration_seconds_int": 2520,
            "time_awake_during_sleep_seconds_int": 1800,
            "time_to_fall_asleep_seconds_int": 600,
        },
        "scores": {"sleep_efficiency_1_100_score_int": 90},
    }}}}
    f = normalize_rook_payload("p1", payload)
    assert f["date"] == date(2026, 11, 11)
    assert f["sleep_duration_hours"] == 7.0
    assert f["sleep_stage_deep_pct"] == 0.1
    assert f["waso_min"] == 30.0 and f["sleep_latency_min"] == 10.0
    assert f["sleep_efficiency"] == 0.9


def test_nested_physical_and_body():
    payload = {"physical_health": {"summary": {"physical_summary": {
        "metadata": {"datetime_string": "2026-11-11T00:00:00Z"},
        "distance": {"steps_int": 4800, "traveled_distance_meters_float": 3500.5},
        "calories": {"active_calories_kcal_float": 310.2},
        "heart_rate": {"hr_resting_bpm_int": 74, "hr_avg_bpm_int": 95, "hrv_avg_rmssd_float": 33.5},
        "oxygenation": {"saturation_avg_percentage_int": 97},
        "activity": {"moderate_activity_seconds_int": 1800, "vigorous_activity_seconds_int": 600},
    }}}}
    f = normalize_rook_payload("p1", payload)
    assert f["steps"] == 4800 and f["distance_meters"] == 3500.5
    assert f["resting_hr_bpm"] == 74.0 and f["avg_hr_day_bpm"] == 95.0
    assert f["hrv_rmssd_ms"] == 33.5 and f["spo2_avg_pct"] == 97.0
    assert f["active_calories_kcal"] == 310.2 and f["workout_minutes"] == 40.0
    assert f["icd_index"] == compute_icd(95.0, 4800)
    assert "sleep_duration_hours" not in f


def test_flat_payload():
    f = normalize_rook_payload("p1", {
        "date": "2026-11-12", "steps": 6000, "resting_heart_rate": 68, "average_heart_rate": 82,
        "hrv": 41, "sleep_duration": 21600, "deep_sleep_duration": 3240,
        "screen_time_min": 150, "caffeine_mg": 95, "alcohol_units": 0.5,
    })
    assert f["date"] == date(2026, 11, 12)
    assert f["resting_hr_bpm"] == 68.0 and f["hrv_rmssd_ms"] == 41.0
    assert f["sleep_duration_hours"] == 6.0 and f["sleep_stage_deep_pct"] == 0.15
    assert f["screen_time_min"] == 150.0 and f["caffeine_mg"] == 95.0 and f["alcohol_units"] == 0.5


def test_user_id_extraction_order():
    assert extract_user_id({"user_id": "a", "client_uuid": "c"}) == "a"
    assert extract_user_id({"user": {"user_id": "n"}}) == "n"
    assert extract_user_id({"client_uuid": "c"}) == "c"
    assert extract_user_id({}) == DEFAULT_PATIENT_ID


def test_data_array_split():
    payload = {"user_id": "u", "data_structure": "physical_summary",
               "data": [{"date": "2026-11-10", "steps": 1}, {"date": "2026-11-11", "steps": 2}]}
    records = extract_records(payload)
    assert len(records) == 2 and records[1]["user_id"] == "u"
    assert normalize_rook_payload("p", records[1])["steps"] == 2
