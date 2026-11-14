"""Cliente httpx assíncrono da ROOK REST API (autenticação HTTP Basic client_uuid:secret)."""

import base64
import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from config import (
    ROOK_PRODUCTION_BASE_URL,
    ROOK_SANDBOX_BASE_URL,
    is_placeholder,
    settings,
)

logger = logging.getLogger(__name__)

# Endpoints de summaries processados por pilar (confirme no portal/docs da ROOK para sua versão)
PILLAR_SUMMARY_PATHS = {
    "sleep_health": "/v2/processed_data/sleep_health/summary",
    "physical_health": "/v2/processed_data/physical_health/summary",
    "body_health": "/v2/processed_data/body_health/summary",
}

MOBILE_ONLY_SOURCES = {"apple_health", "health_connect"}


def is_mobile_only_source(data_source: str) -> bool:
    norm = (data_source or "").strip().lower().replace(" ", "_").replace("-", "_")
    return norm in MOBILE_ONLY_SOURCES


class RookClient:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self._explicit_base_url = base_url.rstrip("/") if base_url else None
        self.base_url = (base_url or settings.ROOK_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.HTTP_CLIENT_TIMEOUT_SEC

    def _secret(self) -> str:
        if not is_placeholder(settings.ROOK_SECRET_KEY):
            return settings.ROOK_SECRET_KEY
        return settings.ROOK_CLIENT_SECRET

    def _has_credentials(self) -> bool:
        return not (is_placeholder(settings.ROOK_CLIENT_UUID) or is_placeholder(self._secret()))

    def _headers(self) -> Dict[str, str]:
        token = base64.b64encode(
            f"{settings.ROOK_CLIENT_UUID}:{self._secret()}".encode("utf-8")
        ).decode("ascii")
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    def _candidate_base_urls(self) -> List[str]:
        primary = (self._explicit_base_url or settings.ROOK_API_BASE_URL).rstrip("/")
        urls = [primary]
        if primary == ROOK_PRODUCTION_BASE_URL:
            urls.append(ROOK_SANDBOX_BASE_URL)
        elif primary == ROOK_SANDBOX_BASE_URL:
            urls.append(ROOK_PRODUCTION_BASE_URL)
        return urls

    async def fetch_summary(
        self, user_id: str, pillar: str, day: date
    ) -> List[Dict[str, Any]]:
        """Busca o summary diário de um pilar. Retorna lista de payloads (vazia em caso de erro)."""
        if not self._has_credentials():
            logger.debug("ROOK_CLIENT_UUID/ROOK_SECRET_KEY não configurados; pulando fetch_summary.")
            return []
        params = {"user_id": user_id, "date": day.isoformat()}
        for base in self._candidate_base_urls():
            url = f"{base}{PILLAR_SUMMARY_PATHS[pillar]}"
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=self._headers(), params=params)
                if resp.status_code == 200:
                    body = resp.json()
                    if body is None:
                        return []
                    return body if isinstance(body, list) else [body]
                logger.warning(
                    "ROOK %s (%s) retornou %d para user %s: %s",
                    pillar, base, resp.status_code, user_id, resp.text[:200],
                )
            except httpx.RequestError as exc:
                logger.warning("Falha de rede ao consultar ROOK (%s): %s", url, exc)
        return []

    async def get_authorizer(self, user_id: str, data_source: str) -> Optional[Dict[str, Any]]:
        """Status/URL de autorização OAuth para fontes baseadas em API (Garmin, Oura, Fitbit...)."""
        if is_mobile_only_source(data_source):
            logger.info("Fonte mobile-only (%s) solicitada para %s; usando modo SDK/Sandbox.", data_source, user_id)
            return None
        if not self._has_credentials():
            logger.warning("ROOK_CLIENT_UUID/ROOK_SECRET_KEY não configurados para consultar authorizer.")
            return None

        for base in self._candidate_base_urls():
            url = f"{base}/api/v1/user_id/{user_id}/data_source/{data_source}/authorizer"
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, headers=self._headers())
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data
                logger.warning(
                    "Authorizer ROOK (%s) retornou %d para user=%s source=%s",
                    base, resp.status_code, user_id, data_source,
                )
            except httpx.RequestError as exc:
                logger.warning("Falha de rede ao consultar authorizer ROOK (%s): %s", url, exc)
        return None


rook_client = RookClient()
