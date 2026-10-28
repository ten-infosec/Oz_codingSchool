from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, Path, UploadFile, status

from app.core.dependencies import CurrentMedicalStaff, CurrentStaff, DbSession
from app.schemas.ai_analysis_list import AIAnalysisListItem
from app.schemas.medical_record import MedicalRecordDetailResponse, MedicalRecordListItem
from app.services import ai_analysis_list_service, medical_record_service


# ===== Medical Records (담당: 엄태은) =====
# 화면(static/apis.js) 주소에 맞춰 /api/v1 아래에 직접 경로를 둔다


router = APIRouter(prefix="/api/v1", tags=["medical-records"])


@router.post(
    "/medical-records",
    summary="진료기록 등록",
    status_code=status.HTTP_201_CREATED,
    response_model=MedicalRecordDetailResponse,
)
async def create_medical_record(
    user: CurrentMedicalStaff,
    db: DbSession,
    # 파일이 있어서 JSON이 아니라 form-data로 받는다
    # 칸마다 Form()으로 받는 방식 (Pydantic 모델 + Form()에 파일을 따로 받으면 422가 나는 함정 회피)
    patient_id: Annotated[int, Form()],
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptoms: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File(description="흉부 X-ray 이미지 (jpeg, png, 최대 10MB)")],
    shooting_datetime: Annotated[datetime | None, Form()] = None,
):
    return await medical_record_service.create_record(
        db, user, patient_id, chart_number, symptoms, xray_image, shooting_datetime
    )


@router.get(
    "/patients/{patient_id}/medical-records",
    summary="진료기록 목록 조회",
    response_model=list[MedicalRecordListItem],
)
async def list_medical_records(patient_id: int, user: CurrentStaff, db: DbSession):
    return await medical_record_service.list_records(db, patient_id)


@router.get(
    "/medical-records/{record_id}",
    summary="진료기록 상세 조회",
    response_model=MedicalRecordDetailResponse,
)
async def get_medical_record(record_id: int, user: CurrentStaff, db: DbSession):
    return await medical_record_service.get_record(db, record_id)


# ===== AI 예측 결과 목록 조회 (6일차, 담당: 김민준) =====
# POST /medical-records/{record_id}/predict는 다른 팀원이 담당한다.
@router.get(
    "/medical-records/{record_id}/analyses",
    summary="AI 예측 결과 목록 조회",
    description="진료기록에 저장된 AI 분석 결과를 수행 일시 최신순으로 조회합니다.",
    response_model=list[AIAnalysisListItem],
)
async def list_medical_record_analyses(
    record_id: Annotated[int, Path(ge=1)],
    user: CurrentStaff,
    db: DbSession,
) -> list[AIAnalysisListItem]:
    return await ai_analysis_list_service.list_analyses(db, record_id)
