"""REQ-PRED-002: return saved analyses, do not run AI inference."""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import ai_analysis_list_repository, medical_record_repository
from app.schemas.ai_analysis_list import AIAnalysisListItem


async def list_analyses(
    db: AsyncSession, record_id: int
) -> list[AIAnalysisListItem]:
    record = await medical_record_repository.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    saved = await ai_analysis_list_repository.list_by_record_id(db, record_id)
    return [AIAnalysisListItem.model_validate(item) for item in saved]
