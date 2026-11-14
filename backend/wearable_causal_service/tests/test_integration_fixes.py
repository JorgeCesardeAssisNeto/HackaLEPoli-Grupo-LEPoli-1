from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import models  # noqa: F401
from config import settings
from database import _prepare_engine_config, get_db
from main import app
from models.base import Base
from models.causal_results import CausalEvaluation, ClinicalAlert
from models.reports import BaselineMetric, ReportComparison, ReportFinding, ReportSession
from models.wearable_metrics import WearableDailyMetric
from schemas.interservice import FHIRObservationPoint, FHIRLabEvolutionResponse
from services.causal_engine import CausalInferenceEngine, causal_engine
from services.ingestion_service import ingest_and_evaluate
from tasks import polling


@pytest_asyncio.fixture
async def mem_client():
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        ac.maker = maker
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


def test_postgres_sslmode_stripped_for_asyncpg():
    url, kwargs = _prepare_engine_config(
        "postgresql+asyncpg://user:pass@host.render.com/openhealth?sslmode=require&channel_binding=require"
    )
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert kwargs == {"ssl": "require"}


@pytest.mark.asyncio
async def test_all_tables_including_reports_persist_cleanly(db_session: AsyncSession):
    metric = WearableDailyMetric(patient_id="pt-rep", date=date(2026, 11, 10), steps=5000)
    db_session.add(metric)
    await db_session.flush()

    ev = CausalEvaluation(
        metric_id=metric.id,
        target_id="TARGET_1_DEEP_SLEEP",
        is_anomaly=True,
        is_confounded=True,
        confounders_detected=["BAIXO_VOLUME_PASSOS_DIARIOS_MENOR_6500"],
        mitigation_verdict="MITIGATED",
        protocol_applied="Protocolo teste",
        clinical_verdict="Veredito teste",
    )
    db_session.add(ev)
    await db_session.flush()

    sess_d1 = ReportSession(
        patient_id="pt-rep", dia=1, tipo="BASELINE", data_referencia=date(2026, 11, 10)
    )
    db_session.add(sess_d1)
    await db_session.flush()

    base = BaselineMetric(
        session_id=sess_d1.id,
        patient_id="pt-rep",
        origem="WEARABLE",
        codigo_metrica="hrv_rmssd_ms",
        nome_metrica="HRV RMSSD",
        valor_baseline=48.0,
    )
    db_session.add(base)
    await db_session.flush()

    sess_d2 = ReportSession(
        patient_id="pt-rep",
        dia=2,
        tipo="COMPARATIVO",
        data_referencia=date(2026, 11, 11),
        baseline_session_id=sess_d1.id,
    )
    db_session.add(sess_d2)
    await db_session.flush()

    comp = ReportComparison(
        session_id=sess_d2.id,
        baseline_id=base.id,
        valor_atual=35.0,
        delta_abs=-13.0,
        delta_pct=-27.1,
        fora_da_faixa=True,
        tendencia="CAIU",
        status="ALERTA",
    )
    finding = ReportFinding(
        session_id=sess_d2.id,
        target_id="TARGET_1_DEEP_SLEEP",
        causal_evaluation_id=ev.id,
        metricas_envolvidas=["sleep_stage_deep_pct"],
        descricao="Achado teste",
        nivel="INFO",
    )
    db_session.add_all([comp, finding])
    await db_session.commit()

    saved = (await db_session.execute(select(ReportFinding))).scalars().all()
    assert len(saved) == 1 and saved[0].causal_evaluation_id == ev.id


@pytest.mark.asyncio
async def test_rolling_window_uses_most_recent_records_beyond_30_days(db_session: AsyncSession, monkeypatch):
    """Regressão: com >30 dias salvos, a janela deve pegar os ÚLTIMOS dias (desc+reversed), não os primeiros 30."""
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    start = date(2026, 10, 1)
    # 31 dias normais (HRV 55) seguidos por 4 dias com HRV < 38 e sono bom >= 6h
    for i in range(34):
        hrv = 55.0 if i < 31 else 31.0
        db_session.add(
            WearableDailyMetric(
                patient_id="pt-long",
                date=start + timedelta(days=i),
                steps=8500,
                resting_hr_bpm=62.0,
                avg_hr_day_bpm=78.0,
                hrv_rmssd_ms=hrv,
                sleep_duration_hours=7.5,
                sleep_stage_deep_pct=0.20,
                alcohol_units=0.0,
            )
        )
    await db_session.commit()

    # Ingestão do 35º dia (4º dia consecutivo com HRV baixa)
    _, alerts_count = await ingest_and_evaluate(
        db_session,
        "pt-long",
        {
            "date": start + timedelta(days=34),
            "steps": 8500,
            "resting_hr_bpm": 62.0,
            "avg_hr_day_bpm": 78.0,
            "hrv_rmssd_ms": 30.0,
            "sleep_duration_hours": 7.8,
            "sleep_stage_deep_pct": 0.21,
            "alcohol_units": 0.0,
        },
    )
    await db_session.commit()

    assert alerts_count >= 1
    alerts = (await db_session.execute(select(ClinicalAlert).where(ClinicalAlert.patient_id == "pt-long"))).scalars().all()
    assert any(a.target_id == "TARGET_3_INFLAMMATION_HRV" for a in alerts)


@pytest.mark.asyncio
async def test_target_4_normal_ferritin_wording_is_accurate():
    mock_fhir = AsyncMock()
    mock_fhir.get_biomarker_evolution.return_value = FHIRLabEvolutionResponse(
        codigo_loinc="2276-4",
        serie_temporal=[FHIRObservationPoint(valor_numerico=97.5, status_classificacao="VERDE")],
    )
    engine = CausalInferenceEngine(fhir_client=mock_fhir)
    res = await engine.evaluate_target_4_anemia_load(
        "pt-janaina", {"avg_hr_day_bpm": 96.0, "steps": 3000, "caffeine_mg": 0.0}
    )
    assert res.trigger_alert is True
    assert "97.5 ng/mL" in res.clinical_verdict
    assert "limítrofe/baixa" not in res.clinical_verdict


@pytest.mark.asyncio
async def test_causal_evaluate_respects_days_window(mem_client, monkeypatch):
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    start = date(2026, 11, 1)
    async with mem_client.maker() as s:
        # 5 dias iniciais normais + 4 dias finais com HRV < 38 ms e sono >= 6h
        for i in range(9):
            hrv = 55.0 if i < 5 else 31.0
            s.add(
                WearableDailyMetric(
                    patient_id="pt-win",
                    date=start + timedelta(days=i),
                    steps=8000,
                    resting_hr_bpm=62.0,
                    avg_hr_day_bpm=78.0,
                    hrv_rmssd_ms=hrv,
                    sleep_duration_hours=7.5,
                    sleep_stage_deep_pct=0.20,
                    alcohol_units=0.0,
                )
            )
        await s.commit()

    ev = await mem_client.post("/causal/evaluate/pt-win?days=4")
    assert ev.status_code == 200
    body = ev.json()
    assert body["days_analyzed"] == 4
    t3 = next(t for t in body["targets_evaluated"] if t["target_id"] == "TARGET_3_INFLAMMATION_HRV")
    assert t3["trigger_alert"] is True
    assert t3["mitigation_verdict"] == "CLINICAL_ANOMALY"


@pytest.mark.asyncio
async def test_manual_ingest_evaluate_and_health_endpoints(mem_client, monkeypatch):
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    h = await mem_client.get("/health")
    assert h.status_code == 200 and h.json()["status"] == "healthy"
    hr = await mem_client.get("/health/ready")
    assert hr.status_code == 200 and hr.json()["database_connected"] is True

    m = await mem_client.post(
        "/wearables/metrics/manual",
        json={
            "patient_id": "pt-e2e",
            "date": "2026-11-12",
            "steps": 8200,
            "resting_hr_bpm": 75.0,
            "avg_hr_day_bpm": 80.0,
            "hrv_rmssd_ms": 48.0,
            "sleep_duration_hours": 7.2,
            "sleep_stage_deep_pct": 0.12,
            "screen_time_min": 40.0,
            "caffeine_mg": 20.0,
            "alcohol_units": 0.0,
        },
    )
    assert m.status_code == 201
    assert m.json()["icd_index"] is not None

    ev = await mem_client.post("/causal/evaluate/pt-e2e?days=14")
    assert ev.status_code == 200
    body = ev.json()
    assert body["days_analyzed"] == 1
    assert body["total_anomalies_detected"] >= 2

    alerts_resp = await mem_client.get("/causal/alerts/pt-e2e")
    assert alerts_resp.status_code == 200 and len(alerts_resp.json()) >= 1
    alert_id = alerts_resp.json()[0]["id"]

    patch_resp = await mem_client.patch(f"/causal/alerts/{alert_id}?new_status=NOTIFIED")
    assert patch_resp.status_code == 200 and patch_resp.json()["status"] == "NOTIFIED"

    metrics_resp = await mem_client.get("/metrics")
    assert metrics_resp.status_code == 200 and metrics_resp.json()["total_wearable_metrics_records"] == 1


@pytest.mark.asyncio
async def test_polling_skips_empty_payload_and_splits_data_array(mem_client, monkeypatch):
    from models.mappings import RookUserMapping

    async with mem_client.maker() as s:
        s.add(RookUserMapping(patient_id="pt-poll", rook_user_id="rk-poll", is_active=True))
        await s.commit()

    monkeypatch.setattr(polling, "AsyncSessionLocal", mem_client.maker)
    monkeypatch.setattr(settings, "POLLING_LOOKBACK_DAYS", 0)
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    async def fake_fetch(user_id, pillar, day):
        if pillar == "physical_health":
            return [
                {},  # envelope vazio não deve gravar linha sem métricas
                {"data": [{"date": "2026-11-10", "steps": 7500}, {"date": "2026-11-11", "steps": 8100}]},
            ]
        return []

    monkeypatch.setattr(polling.rook_client, "fetch_summary", fake_fetch)
    res = await polling.poll_daily_wearable_data(target_patient_id="pt-poll")
    assert res["records_processed"] == 2

    async with mem_client.maker() as s:
        rows = (await s.execute(select(WearableDailyMetric).where(WearableDailyMetric.patient_id == "pt-poll"))).scalars().all()
    assert len(rows) == 2


@pytest.mark.asyncio
async def test_authorizer_sandbox_fallback_and_mobile_sources(mem_client, monkeypatch):
    from models.mappings import TerraUserMapping

    monkeypatch.setattr(settings, "ROOK_CLIENT_UUID", "")
    monkeypatch.setattr(settings, "ROOK_SECRET_KEY", "")
    monkeypatch.setattr(settings, "ROOK_CLIENT_SECRET", "")
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    resp = await mem_client.get(
        "/wearables/authorizer/user-sandbox-1/apple_health",
        headers={"Authorization": "Bearer lovable-jwt-token", "X-Service-Token": "svc-123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "user-sandbox-1"
    assert body["data_source"] == "apple_health"
    assert body["authorization_url"] == "https://connections.rook-connect.review/client_uuid/9bc48033-9d8e-45b4-8c6a-1ef162951442/user-sandbox-1" or (
        body["authorization_url"] == "https://connections.rook-connect.review/client_uuid/9bc48033-9d8e-45b4-8c6a-1ef162951442/user_id/user-sandbox-1"
    )
    assert body["connected"] is True
    assert body["mode"] == "oauth_redirect"

    async with mem_client.maker() as s:
        mapping = (await s.execute(select(TerraUserMapping).where(TerraUserMapping.rook_user_id == "user-sandbox-1"))).scalars().first()
        metrics = (await s.execute(select(WearableDailyMetric).where(WearableDailyMetric.patient_id == "user-sandbox-1"))).scalars().all()
    assert mapping is not None and mapping.is_active is True
    assert len(metrics) == 1

    # Immediate causal evaluation works right after authorizer fallback
    ev = await mem_client.post("/causal/evaluate/user-sandbox-1")
    assert ev.status_code == 200


@pytest.mark.asyncio
async def test_authorizer_oauth_redirect_with_sandbox_url_fallback(mem_client, monkeypatch):
    import httpx
    from config import ROOK_PRODUCTION_BASE_URL, ROOK_SANDBOX_BASE_URL

    monkeypatch.setattr(settings, "ROOK_API_BASE_URL", ROOK_PRODUCTION_BASE_URL)
    monkeypatch.setattr(settings, "ROOK_CLIENT_UUID", "uuid-real")
    monkeypatch.setattr(settings, "ROOK_SECRET_KEY", "")
    monkeypatch.setattr(settings, "ROOK_CLIENT_SECRET", "secret-via-alias")

    calls = []

    def mock_handler(request: httpx.Request):
        calls.append(str(request.url))
        if str(request.url).startswith(ROOK_PRODUCTION_BASE_URL):
            return httpx.Response(401, json={"detail": "wrong env"})
        if str(request.url).startswith(ROOK_SANDBOX_BASE_URL):
            return httpx.Response(200, json={"authorization_url": "https://oauth.garmin.com/auth?state=123"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: orig_client(transport=transport, **kw))

    resp = await mem_client.get("/wearables/authorizer/user-oauth-1/garmin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "oauth_redirect"
    assert body["connected"] is False
    assert body["authorization_url"] == "https://oauth.garmin.com/auth?state=123"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_causal_evaluate_inline_ferritin_and_wearables_override(mem_client, monkeypatch):
    fhir_spy = AsyncMock(return_value=None)
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", fhir_spy)

    # 1. Inline ferritin_ng_ml (low: 19.5 ng/mL) + daytime tachycardia & low steps -> CLINICAL_ANOMALY without calling localhost:5000
    resp1 = await mem_client.post(
        "/causal/evaluate/pt-inline-1",
        json={
            "ferritin_ng_ml": 19.5,
            "steps": 3200,
            "avg_hr_day_bpm": 96.0,
            "resting_hr_bpm": 74.0,
            "hrv_rmssd_ms": 42.0,
            "sleep_duration_hours": 7.0,
            "sleep_stage_deep_pct": 18.0,  # percentage > 1 auto-normalized to 0.18
            "caffeine_mg": 10.0,
            "screen_time_min": 45.0,
            "alcohol_units": 0.0,
        },
        headers={"Authorization": "Bearer lovable-token", "X-Service-Token": "tok"},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    t4_1 = next(t for t in data1["targets_evaluated"] if t["target_id"] == "TARGET_4_ANEMIA_LOAD")
    assert t4_1["mitigation_verdict"] == "CLINICAL_ANOMALY"
    assert t4_1["trigger_alert"] is True
    assert "19.5 ng/mL" in t4_1["clinical_verdict"]
    assert fhir_spy.await_count == 0

    # 2. Inline biomarkers list (normal ferritin: 82.0 ng/mL) + high caffeine (130 mg) -> MITIGATED
    resp2 = await mem_client.post(
        "/causal/evaluate/pt-inline-2",
        json={
            "biomarkers": [
                {"name": "Ferritina Sérica", "code": "2276-4", "value": 82.0, "unit": "ng/mL", "status": "NORMAL"}
            ],
            "steps": 3800,
            "avg_hr_day_bpm": 95.0,
            "caffeine_mg": 130.0,
        },
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    t4_2 = next(t for t in data2["targets_evaluated"] if t["target_id"] == "TARGET_4_ANEMIA_LOAD")
    assert t4_2["mitigation_verdict"] == "MITIGATED"
    assert t4_2["trigger_alert"] is False
    assert "82.0 ng/mL" in t4_2["clinical_verdict"]
    assert fhir_spy.await_count == 0


@pytest.mark.asyncio
async def test_webhook_alias_api_webhooks_rook(mem_client, monkeypatch):
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "")
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    resp = await mem_client.post(
        "/api/webhooks/rook",
        json={
            "user_id": "pt-alias-1",
            "date": "2026-11-14",
            "steps": 7400,
            "resting_heart_rate": 66,
            "average_heart_rate": 79,
            "hrv": 44,
        },
        headers={"Authorization": "Bearer lovable-token", "X-Service-Token": "service-secret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "acknowledged"
    assert body["patient_id"] == "pt-alias-1"
    assert body["records_ingested"] == 1


@pytest.mark.asyncio
async def test_service_token_authentication_enforcement(mem_client, monkeypatch):
    monkeypatch.setattr(settings, "SERVICE_API_KEY", "open-health-secret-key")
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "")
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    # 1. Protected routes reject missing/wrong token with 401
    r_unauth_eval = await mem_client.post("/causal/evaluate/pt-auth", json={"ferritin_ng_ml": 25.0})
    assert r_unauth_eval.status_code == 401

    r_wrong_alerts = await mem_client.get(
        "/causal/alerts/pt-auth", headers={"X-Service-Token": "wrong-key"}
    )
    assert r_wrong_alerts.status_code == 401

    r_unauth_manual = await mem_client.post(
        "/wearables/metrics/manual",
        json={"patient_id": "pt-auth", "date": "2026-11-14", "steps": 6000},
    )
    assert r_unauth_manual.status_code == 401

    # 2. Protected routes accept X-Service-Token and Authorization: Bearer <token>
    r_ok_manual = await mem_client.post(
        "/wearables/metrics/manual",
        json={"patient_id": "pt-auth", "date": "2026-11-14", "steps": 6000},
        headers={"X-Service-Token": "open-health-secret-key"},
    )
    assert r_ok_manual.status_code == 201

    r_ok_eval = await mem_client.post(
        "/causal/evaluate/pt-auth",
        json={"ferritin_ng_ml": 25.0},
        headers={"Authorization": "Bearer open-health-secret-key"},
    )
    assert r_ok_eval.status_code == 200

    # 3. Unprotected routes (/health, /, /wearables/webhook, /api/webhooks/rook) remain open without token
    assert (await mem_client.get("/health")).status_code == 200
    assert (await mem_client.get("/")).status_code == 200
    assert (await mem_client.post("/wearables/webhook", json={"user_id": "pt-auth", "steps": 7000})).status_code == 200
    assert (await mem_client.post("/api/webhooks/rook", json={"user_id": "pt-auth", "steps": 7100})).status_code == 200


@pytest.mark.asyncio
async def test_get_patient_wearable_metrics_auto_seeds_7_days_and_supports_alias(mem_client, monkeypatch):
    # Mesmo com SERVICE_API_KEY ativa, GET /wearables/metrics/{patient_id} deve funcionar sem header
    monkeypatch.setattr(settings, "SERVICE_API_KEY", "secret-token-xyz")

    r1 = await mem_client.get("/wearables/metrics/pt-empty-chart")
    assert r1.status_code == 200
    data1 = r1.json()
    assert len(data1) == 7
    # Verifica ordenação por data decrescente
    dates = [row["date"] for row in data1]
    assert dates == sorted(dates, reverse=True)
    assert all(row["icd_index"] is not None for row in data1)

    # Alias /metrics/{patient_id}?days=3
    r2 = await mem_client.get("/metrics/pt-empty-chart?days=3")
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2) == 3
    assert data2[0]["date"] == data1[0]["date"]


@pytest.mark.asyncio
async def test_sync_endpoint_seeds_metrics_and_generates_alerts_when_rook_empty(mem_client, monkeypatch):
    monkeypatch.setattr(polling, "AsyncSessionLocal", mem_client.maker)
    monkeypatch.setattr(polling.rook_client, "fetch_summary", AsyncMock(return_value=[]))
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    r_sync = await mem_client.post("/wearables/sync?patient_id=pt-sync-demo")
    assert r_sync.status_code == 200
    body = r_sync.json()
    assert body["status"] == "success"
    assert body["patient_id"] == "pt-sync-demo"
    assert body["records_processed"] >= 1
    assert body["alerts_generated"] >= 1

    # Chamada com body JSON e sem query param também funciona
    r_sync_body = await mem_client.post("/wearables/sync", json={"patient_id": "pt-sync-demo"})
    assert r_sync_body.status_code == 200
    assert r_sync_body.json()["records_processed"] >= 1
    assert r_sync_body.json()["alerts_generated"] >= 1


@pytest.mark.asyncio
async def test_authorizer_connection_page_url_and_v1_path_fallback(mem_client, monkeypatch):
    import httpx
    from config import DEFAULT_ROOK_CLIENT_UUID, ROOK_PRODUCTION_BASE_URL, ROOK_SANDBOX_BASE_URL

    # 1. Fallback retorna connection_page_url com UUID padrão
    monkeypatch.setattr(settings, "ROOK_CLIENT_UUID", DEFAULT_ROOK_CLIENT_UUID)
    monkeypatch.setattr(settings, "ROOK_SECRET_KEY", "")
    monkeypatch.setattr(settings, "ROOK_CLIENT_SECRET", "")
    monkeypatch.setattr(causal_engine.fhir_client, "get_biomarker_evolution", AsyncMock(return_value=None))

    r_fb = await mem_client.get("/wearables/authorizer/user-conn-1/garmin")
    assert r_fb.status_code == 200
    fb_body = r_fb.json()
    assert fb_body["mode"] == "oauth_redirect"
    assert fb_body["connected"] is True
    expected_conn_url = f"https://connections.rook-connect.review/client_uuid/{DEFAULT_ROOK_CLIENT_UUID}/user_id/user-conn-1"
    assert fb_body["connection_page_url"] == expected_conn_url
    assert fb_body["authorization_url"] == expected_conn_url

    # 2. Quando /api/v1/... retorna 404 e /v1/... retorna 200 com authorizer_url
    monkeypatch.setattr(settings, "ROOK_API_BASE_URL", ROOK_SANDBOX_BASE_URL)
    monkeypatch.setattr(settings, "ROOK_SECRET_KEY", "sandbox-secret")

    def mock_handler(request: httpx.Request):
        url_str = str(request.url)
        if "/api/v1/" in url_str:
            return httpx.Response(404, json={"detail": "not found"})
        if url_str == f"{ROOK_SANDBOX_BASE_URL}/v1/user_id/user-conn-2/data_source/polar/authorizer":
            return httpx.Response(200, json={"authorizer_url": "https://flow.polar.com/oauth2/authorization"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: orig_client(transport=transport, **kw))

    r_v1 = await mem_client.get("/wearables/authorizer/user-conn-2/polar")
    assert r_v1.status_code == 200
    v1_body = r_v1.json()
    assert v1_body["mode"] == "oauth_redirect"
    assert v1_body["authorization_url"] == "https://flow.polar.com/oauth2/authorization"
    assert "connection_page_url" in v1_body


@pytest.mark.asyncio
async def test_clinical_rag_conhecimento_extrair_and_interpret_endpoints(mem_client):
    # 1. GET /api/conhecimento/{analito} (conhecido e genérico)
    r_ferr = await mem_client.get("/api/conhecimento/ferritina")
    assert r_ferr.status_code == 200
    ferr_data = r_ferr.json()
    assert ferr_data["codigo_loinc"] == "2276-4"
    assert "description" in ferr_data
    assert "clinical_significance" in ferr_data
    assert "causal_relationship" in ferr_data

    r_gen = await mem_client.get("/api/conhecimento/homocisteina_especial")
    assert r_gen.status_code == 200
    assert r_gen.json()["status"] == "success"

    # 2. POST /api/extrair com texto de laudo
    r_ext = await mem_client.post(
        "/api/extrair",
        json={
            "text": "Laudo Laboratorial: Ferritina Sérica: 18,4 ng/mL | Hemoglobina: 11,5 g/dL | Glicose de Jejum: 106 mg/dL | PCR: 4,1 mg/L"
        },
    )
    assert r_ext.status_code == 200
    ext_body = r_ext.json()
    assert ext_body["status"] == "success"
    assert len(ext_body["biomarkers"]) == 4
    by_code = {b["code"]: b for b in ext_body["biomarkers"]}
    assert by_code["2276-4"]["value"] == 18.4
    assert by_code["2276-4"]["status"] == "LOW"
    assert by_code["2345-7"]["value"] == 106.0
    assert by_code["2345-7"]["status"] == "HIGH"

    # 3. POST /api/exams/interpret e alias POST /exams/interpret
    r_int = await mem_client.post(
        "/api/exams/interpret",
        json={
            "patient_id": "pt-rag-1",
            "biomarkers": ext_body["biomarkers"],
            "steps": 3600,
            "avg_hr_day_bpm": 96.0,
            "resting_hr_bpm": 75.0,
            "caffeine_mg": 15.0,
            "screen_time_min": 40.0,
        },
    )
    assert r_int.status_code == 200
    int_body = r_int.json()
    assert int_body["risk_level"] in {"MODERATE", "HIGH"}
    assert "summary" in int_body
    assert len(int_body["findings"]) == 4
    assert len(int_body["incongruencies"]) >= 1
    assert isinstance(int_body["urgent_referral"], bool)
    assert "technical_notes" in int_body

    r_int_alias = await mem_client.post(
        "/exams/interpret",
        json={"text": "Ferritina: 85 ng/mL, TSH: 2.1 mUI/L", "avg_hr_day_bpm": 95.0, "steps": 4000},
    )
    assert r_int_alias.status_code == 200
    assert r_int_alias.json()["status"] == "success"


def _build_in_memory_pdf(lines: list[str]) -> bytes:
    """Constrói um PDF válido em memória usando pypdf com fonte Type1 Helvetica para extração real."""
    import io
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)

    font_dict = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_dict})})
    page[NameObject("/Resources")] = resources

    ops = ["BT", "/F1 12 Tf", "50 780 Td"]
    for idx, line in enumerate(lines):
        if idx > 0:
            ops.append("0 -18 Td")
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append(f"({escaped}) Tj")
    ops.append("ET")

    stream = DecodedStreamObject()
    stream.set_data("\n".join(ops).encode("latin-1", errors="ignore"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_two_distinct_pdfs_extract_completely_different_biomarkers(mem_client):
    # PDF 1: Perfil Hematológico (multi-linha com formatação brasileira)
    pdf_1_bytes = _build_in_memory_pdf(
        [
            "Paciente: Maria Silva",
            "Data da Coleta: 10/11/2026",
            "FERRITINA SERICA",
            "Resultado: 12,4 ng/mL",
            "Valores de Referencia: 30,0 a 300,0 ng/mL",
            "HEMOGLOBINA",
            "Valor obtido: 11,2 g/dL   Referencia: 12,0 a 16,5 g/dL",
        ]
    )

    # PDF 2: Perfil Metabólico e Tireoidiano
    pdf_2_bytes = _build_in_memory_pdf(
        [
            "Paciente: Carlos Souza",
            "Data da Coleta: 12/11/2026",
            "GLICOSE DE JEJUM: 108 mg/dL (Ref: 70 a 99 mg/dL)",
            "TSH ULTRA-SENSIVEL",
            "Resultado: 3,8 mUI/L (Referencia: 0,4 a 4,5 mUI/L)",
            "COLESTEROL TOTAL ............. 210 mg/dL",
        ]
    )

    r1 = await mem_client.post(
        "/api/extrair",
        files={"file": ("laudo_hemato.pdf", pdf_1_bytes, "application/pdf")},
    )
    assert r1.status_code == 200
    body1 = r1.json()

    r2 = await mem_client.post(
        "/api/extrair",
        files={"arquivo": ("laudo_metabolico.pdf", pdf_2_bytes, "application/pdf")},
    )
    assert r2.status_code == 200
    body2 = r2.json()

    # Hashes e previews devem ser distintos
    assert body1["document_hash"] != body2["document_hash"]
    assert "FERRITINA" in body1["extracted_text_preview"].upper()
    assert "COLESTEROL" in body2["extracted_text_preview"].upper()

    # Biomarcadores do PDF 1: apenas Ferritina (12.4) e Hemoglobina (11.2)
    b1_map = {b["analito"]: b["value"] for b in body1["biomarkers"]}
    assert set(b1_map.keys()) == {"ferritina", "hemoglobina"}
    assert b1_map["ferritina"] == 12.4
    assert b1_map["hemoglobina"] == 11.2

    # Biomarcadores do PDF 2: apenas Glicose (108.0), TSH (3.8) e Colesterol (210.0)
    b2_map = {b["analito"]: b["value"] for b in body2["biomarkers"]}
    assert set(b2_map.keys()) == {"glicose", "tsh", "colesterol"}
    assert b2_map["glicose"] == 108.0
    assert b2_map["tsh"] == 3.8
    assert b2_map["colesterol"] == 210.0


@pytest.mark.asyncio
async def test_decimal_dot_original_unit_and_lab_date_extraction(mem_client):
    pdf_bytes = _build_in_memory_pdf(
        [
            "Laboratorio Fleury Medicina e Saude",
            "Paciente: Ana Beatriz",
            "Liberado em: 14/11/2026",
            "FERRITINA SERICA: 18.5 ng/mL (Ref: 30.0 a 300.0 ng/mL)",
            "SODIO SERICO: 141.2 mmol/L (Ref: 135 a 145 mmol/L)",
            "POTASSIO SERICO: 4.3 mmol/L (Ref: 3.5 a 5.1 mmol/L)",
            "LEUCOCITOS TOTAIS: 6.450 /mm3 (Ref: 4.000 a 10.000 /mm3)",
        ]
    )

    resp = await mem_client.post(
        "/api/extrair",
        files={"file": ("fleury_laudo.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Verifica extração de laboratório e data de coleta do cabeçalho do PDF
    assert "Fleury" in data["laboratory"]
    assert "Fleury" in data["cabecalho"]["laboratorio"]
    assert data["collection_date"] == "14/11/2026"
    assert data["cabecalho"]["data_coleta"] == "14/11/2026"

    by_analito = {b["analito"]: b for b in data["biomarkers"]}
    # 1. Ponto decimal preservado (18.5 -> 18.5, nunca truncado para 18) e ponto de milhar tratado (6.450 -> 6450.0)
    assert by_analito["ferritina"]["value"] == 18.5
    assert by_analito["sodio"]["value"] == 141.2
    assert by_analito["potassio"]["value"] == 4.3
    assert by_analito["leucocitos"]["value"] == 6450.0

    # 2. Unidade original do PDF preservada ('mmol/L' em vez do padrão 'mEq/L' do dicionário)
    assert by_analito["sodio"]["unit"] == "mmol/L"
    assert by_analito["potassio"]["unit"] == "mmol/L"



