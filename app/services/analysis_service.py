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


async def predict_record(db: AsyncSession, record_id: int) -> tuple[AIAnalysisResult, bool]:
    """(예측 결과, 새로 예측했는지 여부)를 돌려준다. 이미 있으면 False."""
    # 1) 진료기록이 없으면 404
    await get_record_or_404(db, record_id)

    # 2) 같은 진료기록 + 같은 모델 결과가 있으면 AI를 다시 돌리지 않고 그대로 돌려준다 (REQ-PRED-001)
    saved = await analysis_repository.get_by_record_and_model(db, record_id, MODEL_NAME)
    if saved is not None:
        return saved, False

    # 3) 진료기록 등록 때 저장한 X-ray 주소를 실제 파일 경로로 바꾼다
    image = await medical_record_repository.get_first_image(db, record_id)
    try:
        if image is None:
            raise FileNotFoundError
        image_path = media_url_to_path(image.image_url)
        # 4) 예측 (무거운 계산이라 별도 스레드에서 → 그동안 다른 요청을 막지 않음)
        result = await run_in_threadpool(predict, image_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="X-ray 이미지를 찾을 수 없습니다.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI 예측 중 오류가 발생했습니다.",
        )

    # 5) DB 저장. 실패하면 방금 만든 히트맵 파일을 지워서 남는 파일이 없게 한다
    analysis = AIAnalysisResult(
        record_id=record_id,
        is_pneumonia=result.is_pneumonia,
        confidence=result.confidence,
        heatmap_url=result.heatmap_url,
        ai_model=result.ai_model,
    )
    try:
        analysis = await analysis_repository.create(db, analysis)
    except Exception:
        await db.rollback()
        delete_media_file(result.heatmap_url)
        raise
    return analysis, True

# → 저장된 결과가 있으면 재사용하고, 없으면 X-ray로 예측해 저장한 뒤 돌려주겠다


# ===== List (담당: 김민준) =====
# AI 예측 결과 목록 조회(GET /medical-records/{record_id}/analyses)는
# app/apis/medical_records.py + ai_analysis_list_* 파일로 구현됨 (#38)
