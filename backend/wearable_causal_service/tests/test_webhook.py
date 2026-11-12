import hashlib
import hmac
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from config import settings
from routers.webhook import verify_rook_signature


def _sig(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_signature_valid(monkeypatch):
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo")
    body = b'{"user_id":"u1","data_structure":"sleep_summary"}'
    assert verify_rook_signature(body, _sig(body, "segredo")) is True
    assert verify_rook_signature(body, "sha256=" + _sig(body, "segredo")) is True


def test_signature_tampered(monkeypatch):
    monkeypatch.setattr(settings, "ROOK_WEBHOOK_SECRET", "segredo")
    body = b'{"user_id":"u1"}'
    assert verify_rook_signature(b'{"user_id":"u2"}', _sig(body, "segredo")) is False


def test_signature_missing_rejected(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    assert verify_rook_signature(b"{}", None) is False


@pytest.mark.asyncio
async def test_webhook_unauthorized_without_header(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/wearables/webhook", json={"user_id": "u1"})
    assert resp.status_code == 401
