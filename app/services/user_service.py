from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.users import User
from app.repositories import user_repository


# 규칙(중복 검사, 권한 확인, 비밀번호 확인 등)과 흐름을 처리하는 곳
# 공통으로 쓸 수 있는 도구
# - hash_password(평문) → 해시 문자열  /  verify_password(평문, 해시) → True/False
# - user_repository.get_by_id / get_by_email / get_by_phone_number


# ===== Signup / Withdraw (담당: 장성은) =====
from app.models.enums import Role
from app.schemas.user import SignupRequest


async def signup(db: AsyncSession, body: SignupRequest) -> User:
    # 1) 이메일 중복이면 409 (명세 2-3)
    if await user_repository.get_by_email(db, body.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )

    # 2) 휴대폰 번호 중복이면 409 (명세 2-3)
    if await user_repository.get_by_phone_number(db, body.phone_number) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 휴대폰 번호입니다.",
        )

    # 3) 저장할 회원 만들기
    user = User(
        email=body.email,
        # 비밀번호는 그대로 저장하지 않고 argon2로 해싱 (명세 2-4)
        hashed_password=hash_password(body.password),
        name=body.name,
        department=body.department,
        gender=body.gender,
        phone_number=body.phone_number,
        # 가입 직후 권한은 PENDING 고정 (명세 2-4)
        role=Role.PENDING,
        is_active=True,
    )

    # 4) DB에 저장
    return await user_repository.create(db, user)


async def withdraw(db: AsyncSession, user: User) -> None:
    # 회원 탈퇴: DB에서 즉시 삭제 (명세 11-4)
    await user_repository.delete(db, user)


# ===== My Page (담당: 김민준) =====
# - 정보 수정: 보낸 값만 수정 (model_dump(exclude_unset=True)), 휴대폰 중복이면 409
# - 비밀번호 변경: verify_password로 기존 비밀번호 확인 후 hash_password로 저장


# ===== Admin (담당: 여현지) =====
# - 목록 조회: 이메일·이름 검색, 부서 필터
# - 권한 변경: 대상이 없으면 404
