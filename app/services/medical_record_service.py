from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.files import delete_media_file, save_xray_image
from app.models.medical_records import MedicalRecord
from app.models.users import User
from app.models.xray_images import XrayImage
from app.repositories import medical_record_repository
from app.schemas.medical_record import MedicalRecordDetailResponse, MedicalRecordListItem
from app.services.patient_service import get_patient_or_404


# ===== Medical Record Service (담당: 엄태은) =====

SYMPTOM_PREVIEW_LENGTH = 100


def _to_detail(record: MedicalRecord, image: XrayImage | None) -> MedicalRecordDetailResponse:
    return MedicalRecordDetailResponse(
        id=record.id,
        patient_id=record.patient_id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        xray_image_url=image.image_url if image else None,
        shooting_datetime=image.shooting_datetime if image else None,
        created_at=record.created_at,
    )


async def create_record(
    db: AsyncSession,
    uploader: User,
    patient_id: int,
    chart_number: str,
    symptoms: str,
    xray_image: UploadFile,
    shooting_datetime: datetime | None,
) -> MedicalRecordDetailResponse:
    # 1) 검증: 환자 존재(404), 차트 넘버 중복(409)
    await get_patient_or_404(db, patient_id)
    if await medical_record_repository.get_by_chart_number(db, chart_number) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 차트 넘버입니다.",
        )

    # 촬영일시에 시간대(예: 끝의 Z = UTC)가 붙어 오면 서버 시간대(한국 시간)로 바꾼 뒤 시간대 표시를 뗀다
    # → DB의 created_at(서버 시간)과 같은 기준으로 저장해서 9시간 차이가 나지 않게 하겠다
    if shooting_datetime is not None and shooting_datetime.tzinfo is not None:
        shooting_datetime = shooting_datetime.astimezone().replace(tzinfo=None)

    # 2) 파일 저장 (형식 415, 크기 413 검사 포함)
    path, url = await save_xray_image(xray_image)

    # 3) DB 저장. 실패하면 방금 저장한 파일을 지워서 남는 파일이 없게 한다
    record = MedicalRecord(patient_id=patient_id, chart_number=chart_number, symptoms=symptoms)
    image = XrayImage(
        uploader_id=uploader.id,
        image_url=url,
        shooting_datetime=shooting_datetime or datetime.now(),
    )
    try:
        await medical_record_repository.create_with_image(db, record, image)
    except Exception:
        await db.rollback()
        delete_media_file(url)
        raise

    return _to_detail(record, image)


async def list_records(db: AsyncSession, patient_id: int) -> list[MedicalRecordListItem]:
    await get_patient_or_404(db, patient_id)
    records = await medical_record_repository.list_by_patient(db, patient_id)
    items = []
    for record in records:
        symptoms = record.symptoms
        if len(symptoms) > SYMPTOM_PREVIEW_LENGTH:
            symptoms = symptoms[:SYMPTOM_PREVIEW_LENGTH] + "…"
        items.append(
            MedicalRecordListItem(
                id=record.id,
                chart_number=record.chart_number,
                symptoms=symptoms,
                created_at=record.created_at,
            )
        )
    return items


async def get_record(db: AsyncSession, record_id: int) -> MedicalRecordDetailResponse:
    record = await medical_record_repository.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    image = await medical_record_repository.get_first_image(db, record_id)
    return _to_detail(record, image)
