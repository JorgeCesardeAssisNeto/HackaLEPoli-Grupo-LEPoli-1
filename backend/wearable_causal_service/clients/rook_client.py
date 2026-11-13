"""Cliente httpx assíncrono da ROOK REST API (autenticação HTTP Basic client_uuid:secret)."""

import base64
import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from config import settings

logger = logging.getLogger(__name__)

# Endpoints de summaries processados por pilar (confirme no portal/docs da ROOK para sua versão)
PILLAR_SUMMARY_PATHS = {
    "sleep_health": "/v2/processed_data/sleep_health/summary",
    "physical_health": "/v2/processed_data/physical_health/summary",
    "body_health": "/v2/processed_data/body_health/summary",
}


class RookClient:
    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or settings.ROOK_API_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.HTTP_CLIENT_TIMEOUT_SEC

    def _headers(self) -> Dict[str, str]:
        token = base64.b64encode(
            f"{settings.ROOK_CLIENT_UUID}:{settings.ROOK_SECRET_KEY}".encode("utf-8")
        ).decode("ascii")
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    async def fetch_summary(
        self, user_id: str, pillar: str, day: date
    ) -> List[Dict[str, Any]]:
        """Busca o summary diário de um pilar. Retorna lista de payloads (vazia em caso de erro)."""
        url = f"{self.base_url}{PILLAR_SUMMARY_PATHS[pillar]}"
        params = {"user_id": user_id, "date": day.isoformat()}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._headers(), params=params)
            if resp.status_code == 200:
                body = resp.json()
                return body if isinstance(body, list) else [body]
            logger.warning("ROOK %s retornou %d para user %s: %s", pillar, resp.status_code, user_id, resp.text[:200])
        except httpx.RequestError as exc:
            logger.warning("Falha de rede ao consultar ROOK (%s): %s", url, exc)
        return []

    async def get_authorizer(self, user_id: str, data_source: str) -> Optional[Dict[str, Any]]:
        """Status/URL de autorização OAuth para fontes baseadas em API (Garmin, Oura, Fitbit...)."""
        url = f"{self.base_url}/api/v1/user_id/{user_id}/data_source/{data_source}/authorizer"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._headers())
            return resp.json() if resp.status_code == 200 else None
        except httpx.RequestError as exc:
            logger.warning("Falha de rede ao consultar authorizer ROOK: %s", exc)
            return None


rook_client = RookClient()

