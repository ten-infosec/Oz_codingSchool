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
from sqlalchemy import select

from app.models.enums import Gender


async def get_list(
    db: AsyncSession,
    name: str | None = None,
    gender: Gender | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[Patient]:
    # 조건은 모두 AND로 결합한다 (명세 3-4). 값이 없는 조건은 걸지 않는다.
    stmt = select(Patient)

    if name:
        # 이름 부분 일치. autoescape: 검색어의 %, _ 를 일반 문자로 취급
        stmt = stmt.where(Patient.name.contains(name, autoescape=True))
    if gender:
        stmt = stmt.where(Patient.gender == gender)
    if min_age is not None:
        stmt = stmt.where(Patient.age >= min_age)  # 이상
    if max_age is not None:
        stmt = stmt.where(Patient.age <= max_age)  # 이하

    # 최신 등록 순 (명세 3-4)
    stmt = stmt.order_by(Patient.id.desc())

    result = await db.scalars(stmt)
    return list(result.all())


# ===== Update (담당: 엄태은) =====


async def update(db: AsyncSession, patient: Patient, values: dict) -> Patient:
    for key, value in values.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient
