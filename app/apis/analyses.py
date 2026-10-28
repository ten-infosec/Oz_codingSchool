from fastapi import APIRouter, Response, status

from app.core.dependencies import CurrentStaff, DbSession
from app.services import analysis_service


# ===== Router (담당: 엄태은) =====
# 화면(static/apis.js)이 /medical-records/{id}/predict, /medical-records/{id}/analyses를 호출한다
# 권한: 의료인·개발팀·연구자 = 부서와 관계없이 스태프 이상 (REQ-PRED-001, 002)


router = APIRouter(prefix="/api/v1/medical-records", tags=["analyses"])


# ===== POST /{record_id}/predict (담당: 장성은) =====
# AI 폐렴 예측: 새로 예측 201 / 저장된 결과 재사용 200 (response.status_code로 바꾸기)
# response_model=AnalysisResponse (app/schemas/analysis.py, 현지님)


# ===== GET /{record_id}/analyses (담당: 김민준) =====
# AI 예측 결과 목록: response_model=list[AnalysisResponse], 최신순 배열
