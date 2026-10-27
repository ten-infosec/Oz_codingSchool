from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patient


# ===== Common (담당: 엄태은) =====


async def get_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    return await db.get(Patient, patient_id)


# ===== Create / Delete (담당: 장성은) =====
async def create(db: AsyncSession, patient: Patient) -> Patient:
    # 새 환자를 DB에 저장
    db.add(patient)
    await db.commit()
    # DB가 만들어 준 값(id, created_at 등)을 다시 읽어 온다
    await db.refresh(patient)
    return patient


async def delete(db: AsyncSession, patient: Patient) -> None:
    # 환자를 DB에서 바로 삭제 (Hard Delete)
    # 진료기록·X-ray 기록은 외래키 ON DELETE CASCADE로 DB가 함께 삭제한다
    await db.delete(patient)
    await db.commit()


# ===== List (담당: 여현지) =====
# 예: async def get_list(db, name, gender, min_age, max_age) -> list[Patient]


# ===== Update (담당: 엄태은) =====


async def update(db: AsyncSession, patient: Patient, values: dict) -> Patient:
    for key, value in values.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient
