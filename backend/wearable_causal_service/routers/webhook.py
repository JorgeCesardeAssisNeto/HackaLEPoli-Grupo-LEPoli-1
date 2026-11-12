"""Ouvinte de webhooks da ROOK API (validação HMAC via header X-ROOK-HASH)."""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.mappings import RookUserMapping
from schemas.rook import RookWebhookResponse
from services.rook_normalizer import normalize_rook_payload, SUMMARY_STRUCTURES
from services.ingestion_service import ingest_and_evaluate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wearables", tags=["ROOK Wearables Ingestion"])


def verify_rook_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Valida X-ROOK-HASH: HMAC-SHA256 do corpo bruto com o segredo configurado.
    Aceita digest em hex ou base64 (e prefixo opcional 'sha256='). Comparação em tempo constante.
    """
    if not signature_header:
        return settings.DEBUG  # sem assinatura só é aceito em desenvolvimento

    secret = settings.ROOK_WEBHOOK_SECRET or settings.ROOK_CLIENT_SECRET
    if not secret:
        logger.error("Segredo do webhook ROOK não configurado.")
        return False

    received = signature_header.strip()
    if received.lower().startswith("sha256="):
        received = received[7:]

    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    candidates = (digest.hex(), base64.b64encode(digest).decode("ascii"))
    return any(hmac.compare_digest(c, received) for c in candidates)


@router.post(
    "/webhook",
    response_model=RookWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Webhook em tempo real da ROOK API",
)
async def handle_rook_webhook(
    request: Request,
    x_rook_hash: Optional[str] = Header(None, alias="X-ROOK-HASH"),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()
    if not verify_rook_signature(raw_body, x_rook_hash):
        raise HTTPException(status_code=401, detail="Header X-ROOK-HASH ausente ou inválido.")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Payload JSON malformado.")

    rook_user_id = payload.get("user_id")
    if not rook_user_id:
        raise HTTPException(status_code=400, detail="Campo obrigatório user_id ausente.")
    data_structure = str(payload.get("data_structure", "unknown"))

    mapping = (
        await db.execute(select(RookUserMapping).where(RookUserMapping.rook_user_id == rook_user_id))
    ).scalars().first()
    patient_id = mapping.patient_id if mapping else rook_user_id  # user_id padrão = patient_id
    if mapping:
        mapping.last_sync_at = datetime.utcnow()

    # Eventos de alta frequência e demais tipos são reconhecidos (200) mas não consolidados
    if data_structure not in SUMMARY_STRUCTURES:
        await db.commit()
        return RookWebhookResponse(
            status="ignored", data_structure=data_structure, rook_user_id=rook_user_id,
            patient_id=patient_id, records_ingested=0, causal_evaluated=False, alerts_triggered=0,
        )

    fields = normalize_rook_payload(patient_id, payload)
    _, alerts = await ingest_and_evaluate(db, patient_id, fields)
    await db.commit()

    return RookWebhookResponse(
        status="acknowledged", data_structure=data_structure, rook_user_id=rook_user_id,
        patient_id=patient_id, records_ingested=1, causal_evaluated=True, alerts_triggered=alerts,
    )
