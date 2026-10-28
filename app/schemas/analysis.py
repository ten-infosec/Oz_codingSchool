from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ===== Analysis Response (담당: 여현지) =====
# class AnalysisResponse(BaseModel): from_attributes=True
# 칸: id, record_id, is_pneumonia, confidence(float), heatmap_url, ai_model, created_at
