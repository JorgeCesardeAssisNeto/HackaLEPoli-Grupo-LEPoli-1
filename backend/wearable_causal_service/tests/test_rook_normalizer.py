import math
from datetime import date
from services.rook_normalizer import normalize_rook_payload, compute_icd


def test_icd_formula():
    assert compute_icd(95.0, 2000) == round(95.0 / math.log(2001), 2)
    assert compute_icd(90.0, 0) == round(90.0 / math.log(2), 2)
    assert compute_icd(None, 100) is None


def test_normalize_sleep_summary():
    payload = {
        "user_id": "u1",
        "data_structure": "sleep_summary",
        "sleep_health": {"summary": {"sleep_summary": {
            "metadata": {"datetime_string": "2026-11-11T07:00:00Z"},
            "duration": {
                "sleep_duration_seconds_int": 25200,
                "deep_sleep_duration_seconds_int": 2520,
                "time_awake_during_sleep_seconds_int": 1800,
            },
        }}},
    }
    f = normalize_rook_payload("p1", payload)
    assert f["date"] == date(2026, 11, 11)
    assert f["sleep_duration_hours"] == 7.0
    assert f["sleep_stage_deep_pct"] == 0.1
    assert f["waso_min"] == 30.0


def test_normalize_physical_summary():
    payload = {
        "data_structure": "physical_summary",
        "physical_health": {"summary": {"physical_summary": {
            "metadata": {"datetime_string": "2026-11-11T00:00:00Z"},
            "distance": {"steps_int": 4800},
            "heart_rate": {"hr_resting_bpm_int": 74, "hr_avg_bpm_int": 95},
        }}},
    }
    f = normalize_rook_payload("p1", payload)
    assert f["steps"] == 4800 and f["resting_hr_bpm"] == 74.0 and f["avg_hr_day_bpm"] == 95.0
    assert "sleep_duration_hours" not in f

