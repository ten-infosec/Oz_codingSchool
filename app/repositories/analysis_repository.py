from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_results import AIAnalysisResult


# ===== Predict (담당: 장성은) =====
# async def get_by_record_and_model(db, record_id, ai_model) -> AIAnalysisResult | None
# async def create(db, analysis) -> AIAnalysisResult   (add → commit → refresh)


# ===== List (담당: 김민준) =====
# async def list_by_record(db, record_id) -> list[AIAnalysisResult]   (id 내림차순)
