from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_records import MedicalRecord
from app.models.xray_images import XrayImage


# ===== Medical Record Repository (담당: 엄태은) =====


async def get_by_id(db: AsyncSession, record_id: int) -> MedicalRecord | None:
    return await db.get(MedicalRecord, record_id)


async def get_by_chart_number(db: AsyncSession, chart_number: str) -> MedicalRecord | None:
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.chart_number == chart_number)
    )
    return result.scalar_one_or_none()


async def create_with_image(db: AsyncSession, record: MedicalRecord, image: XrayImage) -> None:
    # 진료기록과 이미지를 한 번에 저장 (둘 중 하나라도 실패하면 둘 다 저장 안 됨)
    db.add(record)
    await db.flush()  # record.id를 먼저 받아 온다
    image.record_id = record.id
    db.add(image)
    await db.commit()
    await db.refresh(record)
    await db.refresh(image)


async def get_first_image(db: AsyncSession, record_id: int) -> XrayImage | None:
    result = await db.execute(
        select(XrayImage).where(XrayImage.record_id == record_id).order_by(XrayImage.id).limit(1)
    )
    return result.scalar_one_or_none()


async def list_by_patient(db: AsyncSession, patient_id: int) -> list[MedicalRecord]:
    # 최신 기록이 위로
    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.id.desc())
    )
    return list(result.scalars().all())


async def get_image_urls_by_patient(db: AsyncSession, patient_id: int) -> list[str]:
    # 환자 삭제(성은님) 때 실제 이미지 파일을 지우기 위해, 환자의 모든 X-ray 주소를 모은다
    result = await db.execute(
        select(XrayImage.image_url)
        .join(MedicalRecord, XrayImage.record_id == MedicalRecord.id)
        .where(MedicalRecord.patient_id == patient_id)
    )
    return list(result.scalars().all())
