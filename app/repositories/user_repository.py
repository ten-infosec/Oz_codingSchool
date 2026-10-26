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
