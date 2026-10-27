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
# POST   /api/v1/patients                 환자 정보 등록 (CurrentMedicalStaff, 201)
# DELETE /api/v1/patients/{patient_id}    환자 정보 삭제 (CurrentStaff, 204)


# ===== List / Detail (담당: 여현지) =====
# GET    /api/v1/patients                 환자 목록 조회 (CurrentStaff, 배열)
# GET    /api/v1/patients/{patient_id}    환자 정보 상세 조회 (CurrentStaff)


# ===== Update (담당: 엄태은, 김민준님 결석으로 대신 담당) =====


@router.patch("/{patient_id}", summary="환자 정보 수정", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    body: PatientUpdateRequest,
    user: CurrentStaff,
    db: DbSession,
):
    return await patient_service.update_patient(db, patient_id, body)
