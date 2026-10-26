from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, verify_password
from app.models.users import User
from app.repositories import user_repository


# ===== Auth Service (담당: 엄태은) =====


_inactive_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="비활성화된 사용자입니다.",
)


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await user_repository.get_by_email(db, email)

    # 이메일이 없거나 비밀번호가 틀리면 같은 메시지로 401
    # (어느 쪽이 틀렸는지 알려 주면 가입된 이메일인지 외부에서 알 수 있기 때문)
    if user is None or user.hashed_password is None or not verify_password(
        password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다.",
        )

    if not user.is_active:
        raise _inactive_exception

    return user


async def get_user_from_refresh_token(db: AsyncSession, refresh_token: str | None) -> User:
    relogin_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="다시 로그인해 주세요.",
    )

    # 쿠키가 없으면 401
    if not refresh_token:
        raise relogin_exception

    # 리프레시 토큰 검증 (만료·위조·액세스 토큰을 넣은 경우 모두 None) → 401
    user_id = decode_token(refresh_token, expected_type="refresh")
    if user_id is None:
        raise relogin_exception

    # 탈퇴한 사용자면 401
    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise relogin_exception

    if not user.is_active:
        raise _inactive_exception

    return user
