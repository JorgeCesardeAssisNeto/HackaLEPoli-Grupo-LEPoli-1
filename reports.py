import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, DateTime,
    ForeignKey, Text, JSON, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from models.base import Base


class ReportSession(Base):
    """
    One analysis day for a patient.
    dia=1 -> BASELINE (reference pattern), dia=2 -> COMPARATIVO, dia=3 -> FINAL.
    """
    __tablename__ = "report_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    dia = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)  # BASELINE | COMPARATIVO | FINAL
    data_referencia = Column(Date, nullable=False)

    # Sources used in this session
    diagnostic_report_id = Column(String(36), nullable=True)  # lab report (hemograma)
    wearable_inicio = Column(Date, nullable=True)
    wearable_fim = Column(Date, nullable=True)

    baseline_session_id = Column(String(36), ForeignKey("report_sessions.id"), nullable=True)
    resumo = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    baselines = relationship("BaselineMetric", back_populates="session", cascade="all, delete-orphan")
    comparisons = relationship(
        "ReportComparison", back_populates="session", cascade="all, delete-orphan",
        foreign_keys="ReportComparison.session_id",
    )
    findings = relationship("ReportFinding", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("patient_id", "dia", name="uq_report_session_patient_dia"),
        CheckConstraint("dia IN (1, 2, 3)", name="chk_report_session_dia"),
        CheckConstraint("tipo IN ('BASELINE', 'COMPARATIVO', 'FINAL')", name="chk_report_session_tipo"),
    )


class BaselineMetric(Base):
    """
    Reference value of each metric, fixed on day 1.
    origem=LAB uses codigo_loinc; origem=WEARABLE uses the wearable_daily_metrics column name.
    """
    __tablename__ = "baseline_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("report_sessions.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String(36), nullable=False, index=True)

    origem = Column(String(10), nullable=False)  # LAB | WEARABLE
    codigo_metrica = Column(String(50), nullable=False)  # LOINC (718-7) or column (hrv_rmssd_ms)
    nome_metrica = Column(String(100), nullable=False)
    unidade = Column(String(30), nullable=True)

    valor_baseline = Column(Float, nullable=False)
    desvio_padrao = Column(Float, nullable=True)  # wearable: std over the day-1 samples
    n_amostras = Column(Integer, default=1, nullable=False)
    faixa_ref_min = Column(Float, nullable=True)
    faixa_ref_max = Column(Float, nullable=True)
    tolerancia_pct = Column(Float, default=5.0, nullable=False)  # variation counted as stable

    session = relationship("ReportSession", back_populates="baselines")

    __table_args__ = (
        UniqueConstraint("patient_id", "origem", "codigo_metrica", name="uq_baseline_patient_metric"),
        CheckConstraint("origem IN ('LAB', 'WEARABLE')", name="chk_baseline_origem"),
    )


class ReportComparison(Base):
    """Value of a metric on day 2/3 compared against its day-1 baseline."""
    __tablename__ = "report_comparisons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("report_sessions.id", ondelete="CASCADE"), nullable=False)
    baseline_id = Column(String(36), ForeignKey("baseline_metrics.id", ondelete="CASCADE"), nullable=False)

    valor_atual = Column(Float, nullable=False)
    delta_abs = Column(Float, nullable=False)
    delta_pct = Column(Float, nullable=True)
    z_score = Column(Float, nullable=True)  # (atual - baseline) / desvio_padrao
    fora_da_faixa = Column(Boolean, default=False, nullable=False)
    tendencia = Column(String(10), nullable=False)  # SUBIU | CAIU | ESTAVEL
    status = Column(String(10), nullable=False)  # NORMAL | ATENCAO | ALERTA
    observacao = Column(Text, nullable=True)

    session = relationship("ReportSession", back_populates="comparisons", foreign_keys=[session_id])
    baseline = relationship("BaselineMetric")

    __table_args__ = (
        UniqueConstraint("session_id", "baseline_id", name="uq_comparison_session_baseline"),
        CheckConstraint("tendencia IN ('SUBIU', 'CAIU', 'ESTAVEL')", name="chk_comparison_tendencia"),
        CheckConstraint("status IN ('NORMAL', 'ATENCAO', 'ALERTA')", name="chk_comparison_status"),
    )


class ReportFinding(Base):
    """
    Cross finding between lab and wearable, tied to the causal targets
    (TARGET_1_DEEP_SLEEP ... TARGET_4_ANEMIA_LOAD).
    """
    __tablename__ = "report_findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("report_sessions.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String(50), nullable=False)
    causal_evaluation_id = Column(String(36), ForeignKey("causal_evaluations.id", ondelete="SET NULL"), nullable=True)

    metricas_envolvidas = Column(JSON, nullable=False)  # list of codigo_metrica
    confundidores = Column(JSON, nullable=True)
    descricao = Column(Text, nullable=False)
    nivel = Column(String(10), nullable=False)  # INFO | ATENCAO | ALERTA
    confianca = Column(Float, default=1.0, nullable=False)
    persistiu_desde_dia = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ReportSession", back_populates="findings")

    __table_args__ = (
        Index("idx_report_findings_session_target", "session_id", "target_id"),
        CheckConstraint("nivel IN ('INFO', 'ATENCAO', 'ALERTA')", name="chk_finding_nivel"),
    )

