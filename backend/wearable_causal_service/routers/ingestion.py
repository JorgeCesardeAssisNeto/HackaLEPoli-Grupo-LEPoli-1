"""Vínculo de usuários ROOK, autorização de fontes, ingestão manual e sync sob demanda."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from clients.rook_client import rook_client
from database import get_db
from models.mappings import RookUserMapping
from schemas.metrics import DailyMetricCreate, DailyMetricResponse, MappingResponse
from schemas.rook import RookLinkRequest
from services.ingestion_service import ingest_and_evaluate, upsert_metric
from tasks.polling import poll_daily_wearable_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wearables", tags=["Device Ingestion & Synchronization"])


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
            summary="Status/URL de autorização OAuth da fonte (Garmin, Oura, Fitbit...)")
async def get_authorizer(rook_user_id: str, data_source: str):
    result = await rook_client.get_authorizer(rook_user_id, data_source)
    if result is None:
        raise HTTPException(status_code=502, detail="ROOK API indisponível ou credenciais inválidas.")
    return result


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
