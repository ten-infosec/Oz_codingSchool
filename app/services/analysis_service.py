from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.files import delete_media_file, media_url_to_path
from app.models.ai_analysis_results import AIAnalysisResult
from app.repositories import analysis_repository, medical_record_repository
from worker.model import MODEL_NAME, predict


# ===== Common (담당: 엄태은) =====


async def get_record_or_404(db: AsyncSession, record_id: int):
    # 진료기록이 없으면 404 (예측 실행·결과 목록 공통)
    record = await medical_record_repository.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    return record


# ===== Predict (담당: 장성은) =====
# async def predict_record(db, record_id) -> tuple[AIAnalysisResult, bool]  (결과, 새로 예측했는지)
# 1) get_record_or_404
# 2) analysis_repository.get_by_record_and_model(db, record_id, MODEL_NAME) → 있으면 (그 결과, False)
# 3) medical_record_repository.get_first_image → media_url_to_path(image.image_url)
# 4) result = await run_in_threadpool(predict, image_path)
#    FileNotFoundError → 404 "X-ray 이미지를 찾을 수 없습니다." / 그 외 → 500 "AI 예측 중 오류가 발생했습니다."
# 5) AIAnalysisResult(...)로 저장 → (결과, True). 저장 실패 시 rollback + delete_media_file(result.heatmap_url)


# ===== List (담당: 김민준) =====
# async def list_analyses(db, record_id) -> list[AIAnalysisResult]
# get_record_or_404 → analysis_repository.list_by_record (없으면 빈 배열)
