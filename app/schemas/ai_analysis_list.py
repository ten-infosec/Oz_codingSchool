"""REQ-PRED-002: response schema for stored AI analyses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIAnalysisListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: int
    is_pneumonia: bool
    # This is a percentage (0.00-100.00), NOT a 0-1 probability.
    confidence: float = Field(ge=0, le=100)
    # Optional at API level; current DB column requires a string.
    heatmap_url: str | None
    ai_model: str
    created_at: datetime
