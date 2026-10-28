from fastapi import APIRouter, Response, status

from app.core.dependencies import CurrentStaff, DbSession
from app.services import analysis_service


# ===== Router (담당: 엄태은) =====
# 화면(static/apis.js)이 /medical-records/{id}/predict, /medical-records/{id}/analyses를 호출한다
# 권한: 의료인·개발팀·연구자 = 부서와 관계없이 스태프 이상 (REQ-PRED-001, 002)


router = APIRouter(prefix="/api/v1/medical-records", tags=["analyses"])


# ===== POST /{record_id}/predict (담당: 장성은) =====


from app.schemas.analysis import AnalysisResponse


@router.post(
    "/{record_id}/predict",
    summary="AI 폐렴 예측",
    status_code=status.HTTP_201_CREATED,
    response_model=AnalysisResponse,
)
async def predict_pneumonia(record_id: int, user: CurrentStaff, db: DbSession, response: Response):
    analysis, created = await analysis_service.predict_record(db, record_id)
    # 새로 예측했으면 201 Created, 저장된 결과를 재사용했으면 200 OK
    if not created:
        response.status_code = status.HTTP_200_OK
    return analysis

# → 진료기록의 X-ray로 폐렴을 예측해 돌려주고, 이미 예측한 적이 있으면 저장된 결과를 200으로 돌려주겠다


# ===== GET /{record_id}/analyses (담당: 김민준) =====
# AI 예측 결과 목록 조회(GET /medical-records/{record_id}/analyses)는
# app/apis/medical_records.py + ai_analysis_list_* 파일로 구현됨 (#38)
