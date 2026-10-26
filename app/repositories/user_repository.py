from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User


# ===== Common (담당: 엄태은) =====
# 여러 API에서 같이 쓰는 조회 함수. 필요하면 가져다 쓰기만 하고 수정은 태은에게 말해 주세요.


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    # 기본키로 한 명 조회 (없으면 None)
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


# ===== Signup / Withdraw (담당: 장성은) =====
# 예: async def create(db, ...) -> User / async def delete(db, user) -> None


# ===== My Page (담당: 김민준) =====
# 예: async def update(db, user, ...) -> User / async def update_password(db, user, hashed_password) -> None


# ===== Admin (담당: 여현지) =====
# 예: async def get_list(db, keyword, department) -> list[User] / async def update_role(db, user, role) -> User
from sqlalchemy import func, or_
from app.models.enums import Department, Role

async def get_list(
    db: AsyncSession,
    keyword: str | None,
    department: Department | None,
    offset: int,
    limit: int,
) -> tuple[list[User], int]:
    # 회원 목록 조회 (이메일/이름 검색 + 부서 필터 + 페이지네이션)
    # 반환: (현재 페이지 회원 목록, 조건에 해당하는 전체 회원 수)
    conditions = []
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(or_(User.email.ilike(pattern), User.name.ilike(pattern)))
    if department:
        conditions.append(User.department == department)

    total = await db.scalar(select(func.count()).select_from(User).where(*conditions))

    result = await db.execute(
        select(User).where(*conditions).order_by(User.id).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total or 0


async def get_by_ids(db: AsyncSession, user_ids: list[int]) -> list[User]:
    # 여러 명 한 번에 조회 (존재하지 않는 ID는 결과에서 빠짐)
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return list(result.scalars().all())


async def update_roles(db: AsyncSession, users: list[User], role: Role) -> list[User]:
    # 선택된 회원들의 권한을 한꺼번에 변경
    for user in users:
        user.role = role
    await db.flush()
    return users