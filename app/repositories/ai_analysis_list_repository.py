"""REQ-PRED-002: saved AI analyses are read-only and sorted newest first."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_results import AIAnalysisResult


async def list_by_record_id(
    db: AsyncSession, record_id: int
) -> list[AIAnalysisResult]:
    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(
            AIAnalysisResult.created_at.desc(),
            AIAnalysisResult.id.desc(),
        )
    )
    return list(result.scalars().all())
