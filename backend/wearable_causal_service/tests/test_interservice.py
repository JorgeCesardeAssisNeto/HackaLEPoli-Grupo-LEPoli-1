import httpx
import pytest

from clients.fhir_client import FHIRLabClient
from clients.nhanes_client import NHANESBaselineClient


@pytest.mark.asyncio
async def test_fhir_client_legacy_payload(monkeypatch):
    def mock_handler(request: httpx.Request):
        if "/api/paciente/pt-1/evolucao/2276-4" in str(request.url):
            content = {
                "codigo_loinc": "2276-4",
                "nome_analito": "Ferritina",
                "serie_temporal": [
                    {"data_coleta": "2026-01-01", "valor_numerico": 28.0, "status_classificacao": "AMARELO"}
                ],
            }
            return httpx.Response(200, json=content)
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: orig_client(transport=transport, **kw))

    client = FHIRLabClient(base_url="http://mock-fhir:5000")
    res = await client.get_biomarker_evolution("pt-1", "2276-4")
    assert res is not None
    assert res.codigo_loinc == "2276-4"
    assert res.serie_temporal[0].valor_numerico == 28.0
    assert res.serie_temporal[0].status_classificacao == "AMARELO"


@pytest.mark.asyncio
async def test_fhir_client_real_port_5000_contract(monkeypatch):
    """Valida desserialização exata do JSON emitido por 02_backend/01_core_api/app.py (porta 5000)."""
    real_payload = {
        "paciente": {
            "id": "d045ff67-b5e4-4236-ade7-c7fba167a585",
            "nome": "Janaina de Assis",
            "sexo_biologico": "F",
            "data_nascimento": "2002-05-10",
        },
        "codigo_loinc": "2276-4",
        "nome_exame": "Ferritina",
        "unidade": "ng/mL",
        "faixa_referencia_min": 13.0,
        "faixa_referencia_max": 150.0,
        "total_registros": 1,
        "serie_temporal": [
            {
                "data_coleta": "06/01/2026",
                "data_coleta_iso": "2026-01-06",
                "valor_numerico": 22.5,
                "classificacao": {"codigo": "LIMITROFE", "cor_nome": "Amarelo", "codigo_4": "LIMITROFE"},
                "tendencia": {"possui_historico": True, "seta": "↘", "texto_tendencia": "Queda recente"},
            }
        ],
    }

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json=real_payload))
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: orig_client(transport=transport, **kw))

    client = FHIRLabClient(base_url="http://mock-fhir:5000")
    res = await client.get_biomarker_evolution("d045ff67-b5e4-4236-ade7-c7fba167a585", "2276-4")
    assert res is not None
    assert res.nome_analito == "Ferritina"
    assert res.paciente is not None and res.paciente.sexo == "F"
    assert res.faixa_referencia == {"min": 13.0, "max": 150.0}
    assert res.serie_temporal[0].status_classificacao == "AMARELO"
    assert isinstance(res.serie_temporal[0].tendencia, dict)


@pytest.mark.asyncio
async def test_nhanes_client_calibration_legacy_and_real_port_5055(monkeypatch):
    def mock_handler(request: httpx.Request):
        if "/api/wearables/user/u-legacy" in str(request.url):
            return httpx.Response(
                200,
                json={"calibration": {"fc_esperada_bpm": 68.2, "delta_ind": -2.4}, "r2": 0.864},
            )
        if "/api/wearables/user/U0001" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "wearable_window": {"user_id": "U0001", "resting_hr_bpm": 70.0},
                    "calibration_and_residuals": {
                        "expected_pulse_nhanes": 72.5,
                        "delta_individual_bpm": -2.5,
                    },
                    "models_inference": {"metabolic": {"status": "Normal"}},
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: orig_client(transport=transport, **kw))

    client = NHANESBaselineClient(base_url="http://mock-nhanes:5055")
    legacy = await client.get_user_calibration("u-legacy", days=14)
    assert legacy is not None
    assert legacy.baseline_metrics.expected_resting_hr_bpm == 68.2
    assert legacy.baseline_metrics.delta_individual_bpm == -2.4

    real = await client.get_user_calibration("U0001", days=14)
    assert real is not None
    assert real.user_id == "U0001"
    assert real.baseline_metrics.expected_resting_hr_bpm == 72.5
    assert real.baseline_metrics.delta_individual_bpm == -2.5
    assert "metabolic" in (real.risk_flags or {})
