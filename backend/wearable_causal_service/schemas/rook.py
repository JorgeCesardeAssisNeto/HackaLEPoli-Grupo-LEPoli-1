from typing import Optional
from pydantic import BaseModel, Field


class RookWebhookResponse(BaseModel):
    status: str
    data_structure: str
    rook_user_id: str
    patient_id: Optional[str] = None
    records_ingested: int
    causal_evaluated: bool
    alerts_triggered: int


class RookLinkRequest(BaseModel):
    patient_id: str = Field(..., description="UUID do paciente Open Health")
    rook_user_id: Optional[str] = Field(
        None, max_length=50, description="user_id usado na ROOK; padrão = patient_id"
    )
    data_source: Optional[str] = Field(None, description="Ex.: Garmin, Oura, Apple Health")

