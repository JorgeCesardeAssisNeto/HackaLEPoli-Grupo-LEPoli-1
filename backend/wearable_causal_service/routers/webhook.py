"""Webhook da ROOK API: POST /wearables/webhook (sempre 200 em entregas válidas)."""

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings, is_placeholder
from database import get_db
from models.mappings import RookUserMapping
from schemas.rook import RookWebhookResponse
from services.ingestion_service import ingest_and_evaluate
from services.rook_normalizer import (
    SUMMARY_STRUCTURES,
    extract_records,
    extract_user_id,
    has_metrics,
    normalize_rook_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wearables", tags=["ROOK Wearables Ingestion"])

SIGNATURE_HEADERS = ("x-rook-signature", "rook-signature", "x-rook-hash")


def get_signature_header(request: Request) -> Optional[str]:
    for name in SIGNATURE_HEADERS:
        value = request.headers.get(name)
        if value:
            return value
    return None


def verify_rook_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Política (hackathon-friendly):
      - DEBUG=True, segredo vazio/placeholder ou ausência de header -> aceita;
      - header presente + segredo real configurado -> exige HMAC-SHA256 válido (hex ou base64,
        prefixo 'sha256=' opcional), comparado em tempo constante.
    """
    if settings.DEBUG or not signature_header or is_placeholder(settings.ROOK_WEBHOOK_SECRET):
        return True

    received = signature_header.strip()
    if received.lower().startswith("sha256="):
        received = received[7:]
    digest = hmac.new(settings.ROOK_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).digest()
    candidates = (digest.hex(), base64.b64encode(digest).decode("ascii"))
    return any(hmac.compare_digest(c, received) for c in candidates)


async def _process(db: AsyncSession, payload: Dict[str, Any]) -> RookWebhookResponse:
    rook_user_id = extract_user_id(payload)
    data_structure = str(payload.get("data_structure") or "unknown")

    mapping = (
        await db.execute(select(RookUserMapping).where(RookUserMapping.rook_user_id == rook_user_id))
    ).scalars().first()
    patient_id = mapping.patient_id if mapping else rook_user_id
    if mapping:
        mapping.last_sync_at = datetime.utcnow()

    ingested = alerts_total = 0
    # Eventos de alta frequência (data_structure presente e fora dos summaries) são só reconhecidos
    if payload.get("data_structure") is None or data_structure in SUMMARY_STRUCTURES:
        for record in extract_records(payload):
            fields = normalize_rook_payload(patient_id, record)
            if not has_metrics(fields):
                continue
            _, alerts = await ingest_and_evaluate(db, patient_id, fields)
            ingested += 1
            alerts_total += alerts

    await db.commit()
    return RookWebhookResponse(
        status="acknowledged" if ingested else "ignored",
        data_structure=data_structure,
        rook_user_id=rook_user_id,
        patient_id=patient_id,
        records_ingested=ingested,
        causal_evaluated=ingested > 0,
        alerts_triggered=alerts_total,
    )


@router.post(
    "/webhook",
    response_model=RookWebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Webhook em tempo real da ROOK API",
)
async def handle_rook_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    if not verify_rook_signature(raw_body, get_signature_header(request)):
        raise HTTPException(status_code=401, detail="Assinatura HMAC inválida.")

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Payload JSON malformado.")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload deve ser um objeto JSON.")

    # Sleep e Physical podem chegar simultaneamente para o mesmo (patient_id, date):
    # em corrida na constraint única, refaz uma vez (o segundo merge já enxerga a linha criada).
    try:
        return await _process(db, payload)
    except IntegrityError:
        await db.rollback()
        logger.info("Conflito de upsert concorrente; repetindo processamento do webhook.")
        return await _process(db, payload)
