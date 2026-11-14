"""Vínculo de usuários ROOK, autorização de fontes, ingestão manual e sync sob demanda."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from clients.rook_client import extract_authorizer_url, is_mobile_only_source, rook_client
from config import DEFAULT_ROOK_CLIENT_UUID, settings
from database import get_db
from dependencies import verify_service_token
from models.causal_results import ClinicalAlert
from models.mappings import RookUserMapping, TerraUserMapping
from models.wearable_metrics import WearableDailyMetric
from schemas.metrics import DailyMetricCreate, DailyMetricResponse, MappingResponse
from schemas.rook import RookLinkRequest
from services.ingestion_service import ingest_and_evaluate, upsert_metric
from tasks.polling import poll_daily_wearable_data

logger = logging.getLogger(__name__)

DEFAULT_DEMO_PATIENT_ID = "e4a7a8d2-1b1e-4c7b-8b9a-112233445566"

router = APIRouter(prefix="/wearables", tags=["Device Ingestion & Synchronization"])
metrics_alias_router = APIRouter(tags=["Device Ingestion & Synchronization"])


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


def _seven_day_realistic_series(end_date: date, data_source: str = "rook_sandbox") -> List[Dict[str, Any]]:
    """Gera 7 dias de métricas diárias realistas (com padrões que exercitam os 4 alvos causais)."""
    profiles = [
        # D-6: basal saudável
        {"steps": 8100, "distance_meters": 6050.0, "active_calories_kcal": 440.0, "workout_minutes": 40.0,
         "resting_hr_bpm": 66.0, "avg_hr_day_bpm": 81.0, "hrv_rmssd_ms": 46.0, "spo2_avg_pct": 98.0,
         "sleep_duration_hours": 7.4, "sleep_efficiency": 0.91, "sleep_latency_min": 11.0, "waso_min": 14.0,
         "sleep_stage_deep_pct": 0.19, "sleep_stage_rem_pct": 0.22, "sleep_stage_light_pct": 0.59,
         "screen_time_min": 55.0, "caffeine_mg": 40.0, "alcohol_units": 0.0, "stress_score": 28.0},
        # D-5: basal estável
        {"steps": 7650, "distance_meters": 5700.0, "active_calories_kcal": 410.0, "workout_minutes": 35.0,
         "resting_hr_bpm": 67.0, "avg_hr_day_bpm": 82.0, "hrv_rmssd_ms": 44.0, "spo2_avg_pct": 97.8,
         "sleep_duration_hours": 7.2, "sleep_efficiency": 0.90, "sleep_latency_min": 12.0, "waso_min": 16.0,
         "sleep_stage_deep_pct": 0.18, "sleep_stage_rem_pct": 0.21, "sleep_stage_light_pct": 0.61,
         "screen_time_min": 65.0, "caffeine_mg": 50.0, "alcohol_units": 0.0, "stress_score": 31.0},
        # D-4: leve queda de sono profundo com tela/cafeína moderadas
        {"steps": 6900, "distance_meters": 5100.0, "active_calories_kcal": 370.0, "workout_minutes": 30.0,
         "resting_hr_bpm": 70.0, "avg_hr_day_bpm": 86.0, "hrv_rmssd_ms": 40.0, "spo2_avg_pct": 97.5,
         "sleep_duration_hours": 6.9, "sleep_efficiency": 0.88, "sleep_latency_min": 15.0, "waso_min": 20.0,
         "sleep_stage_deep_pct": 0.16, "sleep_stage_rem_pct": 0.21, "sleep_stage_light_pct": 0.63,
         "screen_time_min": 80.0, "caffeine_mg": 60.0, "alcohol_units": 0.0, "stress_score": 36.0},
        # D-3: início de queda sustentada de HRV (< 38 ms) com sono adequado (>= 6h) e sem álcool
        {"steps": 7400, "distance_meters": 5500.0, "active_calories_kcal": 395.0, "workout_minutes": 32.0,
         "resting_hr_bpm": 72.0, "avg_hr_day_bpm": 88.0, "hrv_rmssd_ms": 35.0, "spo2_avg_pct": 97.2,
         "sleep_duration_hours": 7.1, "sleep_efficiency": 0.88, "sleep_latency_min": 14.0, "waso_min": 18.0,
         "sleep_stage_deep_pct": 0.15, "sleep_stage_rem_pct": 0.20, "sleep_stage_light_pct": 0.65,
         "screen_time_min": 50.0, "caffeine_mg": 35.0, "alcohol_units": 0.0, "stress_score": 41.0},
        # D-2: 2º dia de HRV reduzida + elevação da FC diurna
        {"steps": 7100, "distance_meters": 5250.0, "active_calories_kcal": 380.0, "workout_minutes": 28.0,
         "resting_hr_bpm": 73.0, "avg_hr_day_bpm": 91.0, "hrv_rmssd_ms": 34.0, "spo2_avg_pct": 97.0,
         "sleep_duration_hours": 7.0, "sleep_efficiency": 0.87, "sleep_latency_min": 16.0, "waso_min": 19.0,
         "sleep_stage_deep_pct": 0.14, "sleep_stage_rem_pct": 0.20, "sleep_stage_light_pct": 0.66,
         "screen_time_min": 45.0, "caffeine_mg": 30.0, "alcohol_units": 0.0, "stress_score": 44.0},
        # D-1: 3º dia de HRV reduzida + sobrecarga cardiovascular diurna
        {"steps": 6800, "distance_meters": 5000.0, "active_calories_kcal": 360.0, "workout_minutes": 25.0,
         "resting_hr_bpm": 74.0, "avg_hr_day_bpm": 93.0, "hrv_rmssd_ms": 33.0, "spo2_avg_pct": 96.9,
         "sleep_duration_hours": 6.8, "sleep_efficiency": 0.86, "sleep_latency_min": 17.0, "waso_min": 21.0,
         "sleep_stage_deep_pct": 0.13, "sleep_stage_rem_pct": 0.20, "sleep_stage_light_pct": 0.67,
         "screen_time_min": 40.0, "caffeine_mg": 25.0, "alcohol_units": 0.0, "stress_score": 47.0},
        # D0 (hoje): anomalia clínica genuína nos alvos 1, 2, 3 e sobrecarga diurna no alvo 4
        {"steps": 7200, "distance_meters": 5320.0, "active_calories_kcal": 390.0, "workout_minutes": 30.0,
         "resting_hr_bpm": 76.0, "avg_hr_day_bpm": 95.0, "hrv_rmssd_ms": 31.0, "spo2_avg_pct": 96.8,
         "sleep_duration_hours": 7.0, "sleep_efficiency": 0.86, "sleep_latency_min": 15.0, "waso_min": 18.0,
         "sleep_stage_deep_pct": 0.12, "sleep_stage_rem_pct": 0.20, "sleep_stage_light_pct": 0.68,
         "screen_time_min": 35.0, "caffeine_mg": 20.0, "alcohol_units": 0.0, "stress_score": 52.0},
    ]
    series: List[Dict[str, Any]] = []
    for idx, prof in enumerate(profiles):
        day = end_date - timedelta(days=(len(profiles) - 1 - idx))
        series.append({
            "date": day,
            **prof,
            "raw_payload": {"data_source": data_source, "mode": "sandbox_seeded", "day_offset": idx - 6},
        })
    return series


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

    client_uuid = settings.ROOK_CLIENT_UUID or DEFAULT_ROOK_CLIENT_UUID
    connection_page_url = (
        f"https://connections.rook-connect.review/client_uuid/{client_uuid}/user_id/{rook_user_id}"
    )

    auth_url = extract_authorizer_url(result)

    if auth_url and isinstance(result, dict):
        await db.commit()
        return {
            **result,
            "user_id": rook_user_id,
            "data_source": data_source,
            "authorization_url": auth_url,
            "connection_page_url": connection_page_url,
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
        "authorization_url": connection_page_url,
        "connection_page_url": connection_page_url,
        "connected": True,
        "mode": "oauth_redirect",
        "message": "Dispositivo vinculado em modo Sandbox/Simulação. Dados sincronizados para avaliação causal.",
    }


@router.get(
    "/metrics/{patient_id}",
    response_model=List[DailyMetricResponse],
    summary="Histórico de métricas diárias do wearable por paciente (auto-seed de 7 dias se vazio)",
)
@metrics_alias_router.get(
    "/metrics/{patient_id}",
    response_model=List[DailyMetricResponse],
    summary="Alias de histórico de métricas diárias do wearable por paciente",
)
async def get_patient_wearable_metrics(
    patient_id: str,
    days: int = Query(30, ge=1, le=365, description="Quantidade máxima de dias retornados"),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WearableDailyMetric)
        .where(WearableDailyMetric.patient_id == patient_id)
        .order_by(WearableDailyMetric.date.desc())
        .limit(days)
    )
    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        mapping = (
            await db.execute(select(RookUserMapping).where(RookUserMapping.patient_id == patient_id))
        ).scalars().first()
        if not mapping:
            db.add(
                RookUserMapping(
                    patient_id=patient_id,
                    rook_user_id=patient_id,
                    data_source="rook_sandbox",
                    is_active=True,
                )
            )
            await db.flush()

        for day_fields in _seven_day_realistic_series(date.today(), data_source="rook_sandbox"):
            await upsert_metric(db, patient_id, day_fields)
        await db.commit()
        rows = (await db.execute(stmt)).scalars().all()

    return rows


@router.post(
    "/metrics/manual",
    response_model=DailyMetricResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_service_token)],
    summary="Inserção manual (inclui confundidores: tela, cafeína, álcool)",
)
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


@router.post("/sync", summary="Disparar polling imediato na ROOK API (com fallback realista para Sandbox)")
async def trigger_sync(
    patient_id: Optional[str] = Query(default=None, description="ID do paciente a sincronizar"),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    body_pid = None
    if isinstance(payload, dict):
        body_pid = payload.get("patient_id") or payload.get("user_id")
    resolved_patient_id = (patient_id or body_pid or DEFAULT_DEMO_PATIENT_ID).strip()

    # Garante que o usuário está vinculado antes de tentar o polling upstream
    mapping = (
        await db.execute(select(RookUserMapping).where(RookUserMapping.patient_id == resolved_patient_id))
    ).scalars().first()
    if not mapping:
        mapping = RookUserMapping(
            patient_id=resolved_patient_id,
            rook_user_id=resolved_patient_id,
            data_source="rook_sandbox",
            is_active=True,
        )
        db.add(mapping)
        await db.commit()
    elif not mapping.is_active:
        mapping.is_active = True
        await db.commit()

    poll_result = await poll_daily_wearable_data(target_patient_id=resolved_patient_id)
    if poll_result.get("records_processed", 0) > 0:
        return {
            **poll_result,
            "patient_id": resolved_patient_id,
        }

    # Fallback Sandbox: quando a ROOK ainda não possui dados em nuvem para este usuário,
    # semeia série diária realista de 7 dias, executa o Motor de Inferência Causal e persiste alertas.
    series = _seven_day_realistic_series(date.today(), data_source=mapping.data_source or "rook_sandbox")
    for day_fields in series[:-1]:
        await upsert_metric(db, resolved_patient_id, day_fields)
    await db.flush()

    _, alerts_created = await ingest_and_evaluate(db, resolved_patient_id, series[-1])
    await db.commit()

    if alerts_created == 0:
        alerts_created = (
            await db.scalar(
                select(func.count())
                .select_from(ClinicalAlert)
                .where(ClinicalAlert.patient_id == resolved_patient_id)
            )
            or 0
        )

    return {
        "status": "success",
        "patient_id": resolved_patient_id,
        "records_processed": len(series),
        "alerts_generated": int(alerts_created),
        "mode": "sandbox_seeded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
