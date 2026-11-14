"""Fluxo único de ingestão: upsert da métrica diária + execução do DAG causal + alertas."""

from typing import Any, Dict, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.wearable_metrics import WearableDailyMetric
from services.rook_normalizer import compute_icd
from services.causal_engine import causal_engine
from services.alert_service import alert_service


def _row_to_dict(row: WearableDailyMetric) -> Dict[str, Any]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


async def upsert_metric(
    session: AsyncSession, patient_id: str, fields: Dict[str, Any]
) -> WearableDailyMetric:
    """Mescla campos parciais na linha (patient_id, date); None nunca sobrescreve valor existente."""
    stmt = select(WearableDailyMetric).where(
        and_(
            WearableDailyMetric.patient_id == patient_id,
            WearableDailyMetric.date == fields["date"],
        )
    )
    row = (await session.execute(stmt)).scalars().first()
    if row is None:
        row = WearableDailyMetric(patient_id=patient_id, date=fields["date"])
        session.add(row)
    for key, value in fields.items():
        if value is not None and key not in ("patient_id", "date") and hasattr(row, key):
            setattr(row, key, value)
    row.icd_index = compute_icd(row.avg_hr_day_bpm, row.steps)
    await session.flush()
    return row


async def ingest_and_evaluate(
    session: AsyncSession, patient_id: str, fields: Dict[str, Any]
) -> Tuple[WearableDailyMetric, int]:
    """Persiste a métrica, roda os 4 alvos causais e grava avaliações/alertas. Retorna (métrica, nº alertas)."""
    row = await upsert_metric(session, patient_id, fields)

    hist_stmt = (
        select(WearableDailyMetric)
        .where(
            and_(
                WearableDailyMetric.patient_id == patient_id,
                WearableDailyMetric.date <= row.date,
            )
        )
        .order_by(WearableDailyMetric.date.desc())
        .limit(30)
    )
    hist_rows = list(reversed((await session.execute(hist_stmt)).scalars().all()))
    history = [_row_to_dict(m) for m in hist_rows]

    evaluations = await causal_engine.evaluate_all_targets(patient_id, _row_to_dict(row), history)
    alerts = await alert_service.persist_evaluations_and_alerts(session, patient_id, row.id, evaluations)
    return row, len(alerts)

