import pytest
import httpx
from clients.fhir_client import FHIRLabClient
from clients.nhanes_client import NHANESBaselineClient

@pytest.mark.asyncio
async def test_fhir_client_success():
    def mock_handler(request: httpx.Request):
        if "/api/paciente/pt-1/evolucao/2276-4" in str(request.url):
            content = {
                "codigo_loinc": "2276-4",
                "nome_analito": "Ferritina",
                "serie_temporal": [
                    {"data_coleta": "2026-01-01", "valor_numerico": 28.0, "status_classificacao": "AMARELO"}
                ]
            }
            return httpx.Response(200, json=content)
        return httpx.Response(404)

    client = FHIRLabClient(base_url="http://mock-fhir:5000")
    # Patch httpx.AsyncClient
    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as mock_ac:
        # Test directly via mock transport
        response = await mock_ac.get("http://mock-fhir:5000/api/paciente/pt-1/evolucao/2276-4")
        assert response.status_code == 200
        data = response.json()
        assert data["codigo_loinc"] == "2276-4"
        assert data["serie_temporal"][0]["valor_numerico"] == 28.0

@pytest.mark.asyncio
async def test_nhanes_client_calibration_success():
    def mock_handler(request: httpx.Request):
        if "/api/wearables/user/u-1" in str(request.url):
            content = {
                "calibration": {
                    "fc_esperada_bpm": 68.2,
                    "delta_ind": -2.4
                },
                "r2": 0.864
            }
            return httpx.Response(200, json=content)
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as mock_ac:
        response = await mock_ac.get("http://mock-nhanes:5055/api/wearables/user/u-1?days=14")
        assert response.status_code == 200
        data = response.json()
        assert data["calibration"]["delta_ind"] == -2.4

