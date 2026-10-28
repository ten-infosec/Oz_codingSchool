from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_results import AIAnalysisResult


# ===== Predict (담당: 장성은) =====


async def get_by_record_and_model(
    db: AsyncSession, record_id: int, ai_model: str
) -> AIAnalysisResult | None:
    # 같은 진료기록 + 같은 모델로 이미 저장된 예측 결과가 있는지 찾는다 (REQ-PRED-001)
    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id, AIAnalysisResult.ai_model == ai_model)
        .order_by(AIAnalysisResult.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

# → 이미 예측한 적이 있으면 그 결과를, 없으면 None을 돌려주겠다


async def create(db: AsyncSession, analysis: AIAnalysisResult) -> AIAnalysisResult:
    # 새 예측 결과를 DB에 저장
    db.add(analysis)
    await db.commit()
    # DB가 만들어 준 값(id, created_at)을 다시 읽어 온다
    await db.refresh(analysis)
    return analysis

# → 예측 결과를 저장하고, id와 수행 일시가 채워진 객체를 돌려주겠다


# ===== List (담당: 김민준) =====
# AI 예측 결과 목록 조회(GET /medical-records/{record_id}/analyses)는
# app/apis/medical_records.py + ai_analysis_list_* 파일로 구현됨 (#38)
