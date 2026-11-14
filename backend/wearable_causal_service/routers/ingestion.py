"""Vínculo de usuários ROOK, autorização de fontes, ingestão manual e sync sob demanda."""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from clients.rook_client import is_mobile_only_source, rook_client
from database import get_db
from models.mappings import RookUserMapping, TerraUserMapping
from models.wearable_metrics import WearableDailyMetric
from schemas.metrics import DailyMetricCreate, DailyMetricResponse, MappingResponse
from schemas.rook import RookLinkRequest
from services.ingestion_service import ingest_and_evaluate, upsert_metric
from tasks.polling import poll_daily_wearable_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wearables", tags=["Device Ingestion & Synchronization"])


def _default_sandbox_seed(today: date, data_source: str) -> Dict[str, Any]:
    """Métricas diárias realistas para inicialização imediata do dashboard em modo Sandbox/Simulação."""
    return {
        "date": today,
        "steps": 5200,
        "distance_meters": 3850.0,
        "active_calories_kcal": 320.0,
        "workout_minutes": 25.0,
        "resting_hr_bpm": 74.0,
        "avg_hr_day_bpm": 94.0,
        "hrv_rmssd_ms": 35.0,
        "spo2_avg_pct": 97.0,
        "sleep_duration_hours": 6.5,
        "sleep_efficiency": 0.87,
        "sleep_latency_min": 14.0,
        "waso_min": 28.0,
        "sleep_stage_deep_pct": 0.14,
        "sleep_stage_rem_pct": 0.21,
        "sleep_stage_light_pct": 0.65,
        "screen_time_min": 145.0,
        "caffeine_mg": 110.0,
        "alcohol_units": 0.0,
        "stress_score": 42.0,
        "raw_payload": {"data_source": data_source, "mode": "sandbox_fallback"},
    }


@router.post("/link-user", response_model=MappingResponse, status_code=status.HTTP_201_CREATED,
             summary="Vincular user_id da ROOK a um paciente")
async def link_rook_user(body: RookLinkRequest, db: AsyncSession = Depends(get_db)):
    rook_user_id = body.rook_user_id or body.patient_id
    mapping = (
        await db.execute(select(RookUserMapping).where(RookUserMapping.rook_user_id == rook_user_id))
    ).scalars().first()
    if mapping:
        mapping.patient_id = body.patient_id
        mapping.data_source = body.data_source or mapping.data_source
        mapping.is_active = True
    else:
        mapping = RookUserMapping(
            patient_id=body.patient_id, rook_user_id=rook_user_id,
            data_source=body.data_source, is_active=True,
        )
        db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.get("/mappings", response_model=List[MappingResponse], summary="Listar vínculos")
async def list_mappings(patient_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(RookUserMapping)
    if patient_id:
        stmt = stmt.where(RookUserMapping.patient_id == patient_id)
    return (await db.execute(stmt)).scalars().all()


@router.get("/authorizer/{rook_user_id}/{data_source}",
            summary="Status/URL de autorização OAuth da fonte (Garmin, Oura, Fitbit, Apple Health...)")
async def get_authorizer(
    rook_user_id: str,
    data_source: str,
    db: AsyncSession = Depends(get_db),
):
    # 1. Garante vínculo do usuário na tabela de mapeamento (TerraUserMapping / RookUserMapping)
    mapping = (
        await db.execute(select(TerraUserMapping).where(TerraUserMapping.rook_user_id == rook_user_id))
    ).scalars().first()
    if mapping:
        mapping.data_source = data_source or mapping.data_source
        mapping.is_active = True
    else:
        mapping = TerraUserMapping(
            patient_id=rook_user_id,
            rook_user_id=rook_user_id,
            data_source=data_source,
            is_active=True,
        )
        db.add(mapping)
    await db.flush()
    patient_id = mapping.patient_id

    # 2. Tenta obter URL OAuth real na ROOK (exceto fontes mobile-only ou sem credenciais)
    result = None
    if not is_mobile_only_source(data_source):
        result = await rook_client.get_authorizer(rook_user_id, data_source)

    auth_url = None
    if isinstance(result, dict):
        auth_url = result.get("authorization_url") or result.get("auth_url") or result.get("url")

    if auth_url:
        await db.commit()
        return {
            **result,
            "user_id": rook_user_id,
            "data_source": data_source,
            "authorization_url": auth_url,
            "connected": bool(result.get("connected", False) or result.get("authorized", False)),
            "mode": "oauth_redirect",
        }

    # 3. Fallback Sandbox/Simulação: garante métrica diária para hoje e retorna HTTP 200 OK
    today = date.today()
    existing_today = (
        await db.execute(
            select(WearableDailyMetric).where(
                and_(
                    WearableDailyMetric.patient_id == patient_id,
                    WearableDailyMetric.date == today,
                )
            )
        )
    ).scalars().first()

    if existing_today is None:
        await ingest_and_evaluate(db, patient_id, _default_sandbox_seed(today, data_source))

    await db.commit()
    return {
        "user_id": rook_user_id,
        "data_source": data_source,
        "authorization_url": None,
        "connected": True,
        "mode": "sandbox_fallback",
        "message": "Dispositivo vinculado em modo Sandbox/Simulação. Dados sincronizados para avaliação causal.",
    }


@router.post("/metrics/manual", response_model=DailyMetricResponse, status_code=status.HTTP_201_CREATED,
             summary="Inserção manual (inclui confundidores: tela, cafeína, álcool)")
async def ingest_manual_metric(
    metric_in: DailyMetricCreate, run_causal: bool = True, db: AsyncSession = Depends(get_db)
):
    fields = metric_in.model_dump()
    if run_causal:
        row, _ = await ingest_and_evaluate(db, metric_in.patient_id, fields)
    else:
        row = await upsert_metric(db, metric_in.patient_id, fields)
    await db.commit()
    await db.refresh(row)
    return row


@router.post("/sync", summary="Disparar polling imediato na ROOK API")
async def trigger_sync(patient_id: Optional[str] = None):
    return await poll_daily_wearable_data(target_patient_id=patient_id)
