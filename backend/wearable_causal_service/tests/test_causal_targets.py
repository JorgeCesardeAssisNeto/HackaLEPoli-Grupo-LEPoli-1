import pytest
import math
from unittest.mock import AsyncMock
from services.causal_engine import CausalInferenceEngine
from services.rook_normalizer import compute_icd
from schemas.interservice import FHIRLabEvolutionResponse, FHIRObservationPoint

# Test ICD calculation
def test_compute_icd_formula():
    """Validates the ICD formula: ICD = HR_day / ln(steps + 1)."""
    # 95 bpm, 2000 steps
    expected_denom = math.log(2000 + 1)
    expected_icd = round(95.0 / expected_denom, 2)
    assert compute_icd(95.0, 2000) == expected_icd

    # Zero steps protection: ln(1 + 1) = ln(2)
    zero_steps_icd = compute_icd(90.0, 0)
    assert zero_steps_icd is not None
    assert zero_steps_icd == round(90.0 / math.log(2.0), 2)

    # None handling
    assert compute_icd(None, 5000) is None
    assert compute_icd(90.0, None) is None

# Target 1 Tests
def test_target_1_deep_sleep_normal():
    engine = CausalInferenceEngine()
    metric = {
        "sleep_stage_deep_pct": 0.18,  # >= 16% is normal
        "steps": 8000,
        "alcohol_units": 0.0,
        "waso_min": 20.0
    }
    result = engine.evaluate_target_1_deep_sleep(metric)
    assert result.is_anomaly is False
    assert result.mitigation_verdict == "NORMAL"
    assert result.trigger_alert is False

def test_target_1_deep_sleep_mitigated_by_steps():
    engine = CausalInferenceEngine()
    metric = {
        "sleep_stage_deep_pct": 0.12,  # Anomaly (< 16%)
        "steps": 4200,                # Confounder (< 6500)
        "alcohol_units": 0.0,
        "waso_min": 25.0
    }
    result = engine.evaluate_target_1_deep_sleep(metric)
    assert result.is_anomaly is True
    assert result.is_confounded is True
    assert result.mitigation_verdict == "MITIGATED"
    assert "BAIXO_VOLUME_PASSOS_DIARIOS_MENOR_6500" in result.confounders_detected
    assert result.trigger_alert is False

def test_target_1_deep_sleep_mitigated_by_alcohol():
    engine = CausalInferenceEngine()
    metric = {
        "sleep_stage_deep_pct": 0.10,  # Anomaly (< 16%)
        "steps": 9500,                # High steps
        "alcohol_units": 1.2,         # Confounder (> 0.4)
        "waso_min": 52.0              # Confounder (> 45 min)
    }
    result = engine.evaluate_target_1_deep_sleep(metric)
    assert result.is_anomaly is True
    assert result.is_confounded is True
    assert result.mitigation_verdict == "MITIGATED"
    assert "CONSUMO_ALCOOL_FRAGMENTACAO_WASO" in result.confounders_detected
    assert result.trigger_alert is False

def test_target_1_deep_sleep_clinical_anomaly():
    engine = CausalInferenceEngine()
    metric = {
        "sleep_stage_deep_pct": 0.11,  # Anomaly (< 16%)
        "steps": 8900,                # Clean lifestyle (>= 6500)
        "alcohol_units": 0.0,         # No alcohol
        "waso_min": 18.0
    }
    result = engine.evaluate_target_1_deep_sleep(metric)
    assert result.is_anomaly is True
    assert result.is_confounded is False
    assert result.mitigation_verdict == "CLINICAL_ANOMALY"
    assert result.trigger_alert is True
    assert result.alert_level == "WARNING"

# Target 2 Tests
def test_target_2_metabolic_risk_mitigated_by_screen_and_caffeine():
    engine = CausalInferenceEngine()
    metric = {
        "resting_hr_bpm": 76.0,       # Anomaly (>= 72 bpm)
        "screen_time_min": 145.0,     # Confounder (> 130 min)
        "caffeine_mg": 95.0           # Confounder (> 80 mg)
    }
    result = engine.evaluate_target_2_metabolic_risk(metric, [metric])
    assert result.is_anomaly is True
    assert result.is_confounded is True
    assert result.mitigation_verdict == "MITIGATED"
    assert result.trigger_alert is False

def test_target_2_metabolic_risk_clinical_anomaly():
    engine = CausalInferenceEngine()
    # 14 days of resting HR >= 72 with clean routine (< 130 min screen, < 80 mg caffeine)
    history = [
        {"resting_hr_bpm": 74.0, "screen_time_min": 60.0, "caffeine_mg": 30.0}
        for _ in range(14)
    ]
    curr = {"resting_hr_bpm": 75.0, "screen_time_min": 50.0, "caffeine_mg": 20.0}
    result = engine.evaluate_target_2_metabolic_risk(curr, history)
    assert result.is_anomaly is True
    assert result.is_confounded is False
    assert result.mitigation_verdict == "CLINICAL_ANOMALY"
    assert result.trigger_alert is True
    assert result.recommended_loinc == "4548-4"  # HbA1c

# Target 3 Tests
def test_target_3_inflammation_hrv_transient_drop():
    engine = CausalInferenceEngine()
    metric = {
        "hrv_rmssd_ms": 32.0,            # Anomaly (< 38 ms)
        "sleep_duration_hours": 4.5,     # Confounder (< 6h)
        "alcohol_units": 0.8             # Confounder (> 0.4)
    }
    # 1-day drop only
    result = engine.evaluate_target_3_inflammation_hrv(metric, [metric])
    assert result.is_anomaly is True
    assert result.is_confounded is True
    assert result.mitigation_verdict == "MITIGATED"
    assert result.trigger_alert is False

def test_target_3_inflammation_hrv_4_consecutive_days_rule():
    engine = CausalInferenceEngine()
    # 4 consecutive days of HRV < 38 ms with adequate sleep (>= 6h) and no alcohol
    history = [
        {"hrv_rmssd_ms": 31.0, "sleep_duration_hours": 7.5, "alcohol_units": 0.0},
        {"hrv_rmssd_ms": 33.0, "sleep_duration_hours": 7.8, "alcohol_units": 0.0},
        {"hrv_rmssd_ms": 29.0, "sleep_duration_hours": 7.2, "alcohol_units": 0.0},
        {"hrv_rmssd_ms": 30.0, "sleep_duration_hours": 8.0, "alcohol_units": 0.0},
    ]
    curr = history[-1]
    result = engine.evaluate_target_3_inflammation_hrv(curr, history)
    assert result.is_anomaly is True
    assert result.is_confounded is False
    assert result.mitigation_verdict == "CLINICAL_ANOMALY"
    assert result.trigger_alert is True
    assert result.alert_level == "CRITICAL"
    assert result.recommended_loinc == "30522-7"  # hs-CRP

# Target 4 Tests (Async with FHIR Mock)
@pytest.mark.asyncio
async def test_target_4_anemia_caffeine_mitigation():
    mock_fhir = AsyncMock()
    mock_fhir.get_biomarker_evolution.return_value = FHIRLabEvolutionResponse(
        codigo_loinc="2276-4",
        serie_temporal=[FHIRObservationPoint(valor_numerico=65.0, status_classificacao="VERDE")]
    )
    engine = CausalInferenceEngine(fhir_client=mock_fhir)

    metric = {
        "avg_hr_day_bpm": 96.0,  # > 92 bpm
        "steps": 4100,           # < 6000 steps
        "caffeine_mg": 120.0     # Confounder (> 90 mg)
    }
    result = await engine.evaluate_target_4_anemia_load("patient-123", metric)
    assert result.is_anomaly is True
    assert result.is_confounded is True
    assert result.mitigation_verdict == "MITIGATED"
    assert result.trigger_alert is False

@pytest.mark.asyncio
async def test_target_4_anemia_clinical_anomaly_prior_ferritin_low():
    mock_fhir = AsyncMock()
    # Prior Ferritin low (< 30 ng/mL)
    mock_fhir.get_biomarker_evolution.return_value = FHIRLabEvolutionResponse(
        codigo_loinc="2276-4",
        serie_temporal=[FHIRObservationPoint(valor_numerico=22.0, status_classificacao="AMARELO")]
    )
    engine = CausalInferenceEngine(fhir_client=mock_fhir)

    metric = {
        "avg_hr_day_bpm": 97.0,  # > 92 bpm
        "steps": 3500,           # < 6000 steps
        "caffeine_mg": 20.0      # Low caffeine (<= 90 mg)
    }
    result = await engine.evaluate_target_4_anemia_load("patient-123", metric)
    assert result.is_anomaly is True
    assert result.is_confounded is False
    assert result.mitigation_verdict == "CLINICAL_ANOMALY"
    assert result.trigger_alert is True
    assert result.recommended_loinc == "2276-4"  # Ferritin

