from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patient
from app.repositories import patient_repository
from app.schemas.patient import PatientUpdateRequest


# 공통으로 쓸 수 있는 도구
# - get_patient_or_404(db, patient_id): 환자가 없으면 404
# - app.core.files.delete_media_file(url): 이미지 파일 삭제
# - medical_record_repository.get_image_urls_by_patient(db, patient_id): 환자의 모든 X-ray 주소


# ===== Common (담당: 엄태은) =====


async def get_patient_or_404(db: AsyncSession, patient_id: int) -> Patient:
    patient = await patient_repository.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )
    return patient


# ===== Create / Delete (담당: 장성은) =====
# - 등록: 받은 phone_number를 DB 칸 phone에 저장 (Patient(phone=body.phone_number, ...))
# - 삭제: 이미지 주소를 먼저 모으고 → 환자 삭제(진료기록·이미지 DB는 CASCADE로 함께 삭제) → 파일 삭제


# ===== List / Detail (담당: 여현지) =====
from app.models.enums import Gender


async def list_patients(
    db: AsyncSession,
    name: str | None = None,
    gender: Gender | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[Patient]:
    # 나이 범위가 뒤집혀 있으면 422 (명세 3-3)
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_age는 max_age보다 클 수 없습니다.",
        )

    return await patient_repository.get_list(
        db,
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )


async def get_patient(db: AsyncSession, patient_id: int) -> Patient:
    # 상세 조회: 없는 환자는 get_patient_or_404가 404를 낸다 (명세 4-3)
    return await get_patient_or_404(db, patient_id)


# ===== Update (담당: 엄태은, 김민준님 결석으로 대신 담당) =====


async def update_patient(db: AsyncSession, patient_id: int, body: PatientUpdateRequest) -> Patient:
    patient = await get_patient_or_404(db, patient_id)

    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목(이름, 연락처)을 하나 이상 보내 주세요.",
        )
    # 화면 이름 phone_number → DB 칸 phone
    if "phone_number" in values:
        values["phone"] = values.pop("phone_number")

    return await patient_repository.update(db, patient, values)
