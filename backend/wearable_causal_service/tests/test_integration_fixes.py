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
