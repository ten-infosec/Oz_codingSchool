from fastapi import APIRouter, status

from app.core.dependencies import CurrentMedicalStaff, CurrentStaff, DbSession
from app.schemas.patient import PatientResponse, PatientUpdateRequest
from app.services import patient_service


router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

# 사용 방법
# - 의료인 전용 (환자 등록):   user: CurrentMedicalStaff
# - 스태프 이상 (나머지):      user: CurrentStaff
# - DB 세션:                  db: DbSession
# - 응답:                     response_model=PatientResponse (목록은 list[PatientResponse])


# ===== Create / Delete (담당: 장성은) =====
from app.schemas.patient import PatientCreateRequest


# POST /api/v1/patients 환자 정보 등록 (명세 2번)
@router.post(
    "",
    summary="환자 정보 등록",
    status_code=status.HTTP_201_CREATED,
    response_model=PatientResponse,
)
async def create_patient(
    body: PatientCreateRequest,
    user: CurrentMedicalStaff,
    db: DbSession,
):
    return await patient_service.create_patient(db, body)


# DELETE /api/v1/patients/{patient_id} 환자 정보 삭제 (명세 6번)
@router.delete(
    "/{patient_id}",
    summary="환자 정보 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_patient(patient_id: int, user: CurrentStaff, db: DbSession):
    await patient_service.delete_patient(db, patient_id)
    # 204는 응답 본문이 없어야 하므로 아무것도 return하지 않는다


# ===== List / Detail (담당: 여현지) =====
from fastapi import Query

from app.models.enums import Gender


@router.get("", summary="환자 목록 조회", response_model=list[PatientResponse])
async def list_patients(
    user: CurrentStaff,
    db: DbSession,
    name: str | None = Query(default=None, max_length=100, description="이름 검색 (부분 일치)"),
    gender: Gender | None = Query(default=None, description="성별 필터 (male / female)"),
    min_age: int | None = Query(default=None, ge=0, le=150, description="나이 하한 (이상)"),
    max_age: int | None = Query(default=None, ge=0, le=150, description="나이 상한 (이하)"),
):
    return await patient_service.list_patients(
        db,
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )


@router.get("/{patient_id}", summary="환자 정보 상세 조회", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    user: CurrentStaff,
    db: DbSession,
):
    return await patient_service.get_patient(db, patient_id)


# ===== Update (담당: 엄태은, 김민준님 결석으로 대신 담당) =====


@router.patch("/{patient_id}", summary="환자 정보 수정", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    body: PatientUpdateRequest,
    user: CurrentStaff,
    db: DbSession,
):
    return await patient_service.update_patient(db, patient_id, body)
