from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patient


# ===== Common (담당: 엄태은) =====


async def get_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    return await db.get(Patient, patient_id)


# ===== Create / Delete (담당: 장성은) =====
# 예: async def create(db, patient) -> Patient / async def delete(db, patient) -> None


# ===== List (담당: 여현지) =====
# 예: async def get_list(db, name, gender, min_age, max_age) -> list[Patient]


# ===== Update (담당: 엄태은) =====


async def update(db: AsyncSession, patient: Patient, values: dict) -> Patient:
    for key, value in values.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient
