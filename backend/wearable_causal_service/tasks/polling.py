"""Polling diário (APScheduler) na ROOK REST API para cobrir webhooks perdidos e histórico."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from clients.rook_client import rook_client, PILLAR_SUMMARY_PATHS
from config import settings
from database import AsyncSessionLocal
from models.mappings import RookUserMapping
from services.ingestion_service import ingest_and_evaluate
from services.rook_normalizer import normalize_rook_payload

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_daily_wearable_data(target_patient_id: Optional[str] = None) -> Dict[str, Any]:
    """Para cada usuário ativo, busca os últimos N dias de cada pilar, persiste e avalia o DAG causal."""
    logger.info("[POLLING] Iniciando reconciliação com a ROOK API...")
    processed = alerts_total = 0

    async with AsyncSessionLocal() as session:
        query = select(RookUserMapping).where(RookUserMapping.is_active == True)  # noqa: E712
        if target_patient_id:
            query = query.where(RookUserMapping.patient_id == target_patient_id)
        users: List[RookUserMapping] = (await session.execute(query)).scalars().all()

        for user in users:
            try:
                for offset in range(settings.POLLING_LOOKBACK_DAYS, -1, -1):
                    day = date.today() - timedelta(days=offset)
                    for pillar in PILLAR_SUMMARY_PATHS:
                        for payload in await rook_client.fetch_summary(user.rook_user_id, pillar, day):
                            fields = normalize_rook_payload(user.patient_id, payload, default_date=day)
                            _, alerts = await ingest_and_evaluate(session, user.patient_id, fields)
                            processed += 1
                            alerts_total += alerts
                user.last_sync_at = datetime.utcnow()
                await session.commit()
            except Exception as exc:
                logger.error("[POLLING] Erro no usuário %s: %s", user.rook_user_id, exc)
                await session.rollback()

    logger.info("[POLLING] Concluído: %d payloads, %d alertas.", processed, alerts_total)
    return {
        "status": "success",
        "records_processed": processed,
        "alerts_generated": alerts_total,
        "timestamp": datetime.utcnow().isoformat(),
    }


def start_scheduler() -> None:
    if not settings.ENABLE_BACKGROUND_POLLING:
        logger.info("Polling em background desabilitado.")
        return
    scheduler.add_job(
        poll_daily_wearable_data,
        CronTrigger(hour=settings.POLLING_CRON_HOUR, minute=settings.POLLING_CRON_MINUTE),
        id="daily_wearable_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Polling diário agendado para %02d:%02d.", settings.POLLING_CRON_HOUR, settings.POLLING_CRON_MINUTE)


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
