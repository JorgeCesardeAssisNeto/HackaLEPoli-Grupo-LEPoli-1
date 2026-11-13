import hashlib
import hmac

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config import settings
from database import get_db
from main import app
from models.base import Base
from models.wearable_metrics import WearableDailyMetric
from routers.webhook import verify_rook_signature

PID = "e4a7a8d2-1b1e-4c7b-8b9a-112233445566"


def _sig(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ------------------------------------------------------------------ política de assinatura
def test_signature_valid_with_configured_secret(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo-real")
    body = b'{"user_id":"u1"}'
    assert verify_rook_signature(body, _sig(body, "segredo-real")) is True
    assert verify_rook_signature(body, "sha256=" + _sig(body, "segredo-real")) is True


def test_signature_invalid_rejected_when_secret_configured(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo-real")
    assert verify_rook_signature(b'{"a":1}', "deadbeef") is False


def test_missing_header_allowed(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo-real")
    assert verify_rook_signature(b"{}", None) is True


@pytest.mark.parametrize("secret", ["", "YOUR_ROOK_WEBHOOK_SECRET"])
def test_placeholder_secret_skips_validation(monkeypatch, secret):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", secret)
    assert verify_rook_signature(b"{}", "qualquer") is True


def test_debug_skips_validation(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo-real")
    assert verify_rook_signature(b"{}", "invalido") is True


# ------------------------------------------------------------------ fluxo HTTP com banco em memória
@pytest_asyncio.fixture
async def client():
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


async def test_merge_sleep_then_physical_recomputes_icd(client, monkeypatch):
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "")
    sleep = {
        "user_id": PID, "data_structure": "sleep_summary",
        "sleep_health": {"summary": {"sleep_summary": {
            "metadata": {"datetime_string": "2026-11-11T07:00:00Z"},
            "duration": {"sleep_duration_seconds_int": 25200, "deep_sleep_duration_seconds_int": 4200},
        }}},
    }
    physical = {
        "user_id": PID, "data_structure": "physical_summary",
        "physical_health": {"summary": {"physical_summary": {
            "metadata": {"datetime_string": "2026-11-11T00:00:00Z"},
            "distance": {"steps_int": 8000},
            "heart_rate": {"hr_resting_bpm_int": 60, "hr_avg_bpm_int": 80},
        }}},
    }
    r1 = await client.post("/wearables/webhook", json=sleep)
    r2 = await client.post("/wearables/webhook", json=physical)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json()["records_ingested"] == 1

    async with client.maker() as s:
        rows = (await s.execute(select(WearableDailyMetric))).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.sleep_duration_hours == 7.0 and row.sleep_stage_deep_pct == 0.167  # preservado
    assert row.steps == 8000 and row.avg_hr_day_bpm == 80.0
    assert row.icd_index is not None


async def test_flat_payload_without_user_id_uses_fallback(client, monkeypatch):
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "")
    resp = await client.post("/wearables/webhook", json={
        "date": "2026-11-12", "steps": 5000, "resting_heart_rate": 70, "average_heart_rate": 80,
        "hrv": 45, "sleep_duration": 28800, "caffeine_mg": 40, "alcohol_units": 0,
    })
    assert resp.status_code == 200
    assert resp.json()["patient_id"] == PID


async def test_non_summary_event_is_acknowledged(client):
    resp = await client.post("/wearables/webhook", json={
        "user_id": "u1", "data_structure": "heart_rate_event", "heart_rate_bpm_int": 70,
    })
    assert resp.status_code == 200 and resp.json()["status"] == "ignored"


async def test_bad_signature_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo-real")
    resp = await client.post("/wearables/webhook", json={"user_id": "u1"},
                             headers={"x-rook-signature": "invalida"})
    assert resp.status_code == 401
