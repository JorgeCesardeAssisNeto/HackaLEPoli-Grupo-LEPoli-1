import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Index
from models.base import Base, utc_now_naive


class RookUserMapping(Base):
    """
    Vincula o `user_id` da ROOK (definido por nós, 1-50 caracteres) ao paciente Open Health.
    Por padrão rook_user_id == patient_id.
    """
    __tablename__ = "rook_user_mappings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    rook_user_id = Column(String(50), unique=True, nullable=False, index=True)
    data_source = Column(String(50), nullable=True)  # Garmin, Oura, Apple Health, Health Connect...
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive, nullable=False)

    __table_args__ = (Index("idx_rook_mapping_patient", "patient_id"),)
