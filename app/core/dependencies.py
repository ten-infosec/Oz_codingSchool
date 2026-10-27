from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.security import decode_token
from app.models.enums import Department, Role
from app.models.users import User
from app.repositories import user_repository


# ===== DB Session =====


# API 함수에서 db: DbSession 으로 쓰면 요청마다 세션을 받아 온다
DbSession = Annotated[AsyncSession, Depends(async_get_db)]


# ===== Current User =====


# Authorization: Bearer <토큰> 헤더를 읽는 도구
# auto_error=False: 헤더가 없을 때 FastAPI 기본 에러(403) 대신 우리가 정한 401을 내기 위해
_bearer_scheme = HTTPBearer(auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증 정보가 유효하지 않습니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    # 1) 헤더가 없으면 401
    if credentials is None:
        raise _credentials_exception

    # 2) 액세스 토큰 검증 (만료·위조·종류 불일치면 None) → 401
    user_id = decode_token(credentials.credentials, expected_type="access")
    if user_id is None:
        raise _credentials_exception

    # 3) 토큰 주인이 DB에 없으면(탈퇴 등) 401
    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise _credentials_exception

    # 4) 비활성화 계정이면 403
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다.",
        )

    return user


# 로그인한 사용자 (권한 상관없음, PENDING 포함) → 마이페이지 API에서 사용
CurrentUser = Annotated[User, Depends(get_current_user)]


# ===== Role Check =====


async def get_current_admin(user: CurrentUser) -> User:
    # ADMIN이 아니면 403
    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return user


async def get_current_staff(user: CurrentUser) -> User:
    # STAFF 또는 ADMIN만 통과 (PENDING은 403) → 이후 X-ray 관련 API에서 사용
    if user.role not in (Role.STAFF, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return user


# 관리자 전용 API에서 사용
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
# 스태프 이상 API에서 사용
CurrentStaff = Annotated[User, Depends(get_current_staff)]


# ===== Medical Staff (5일차) =====


async def get_current_medical_staff(user: CurrentUser) -> User:
    # 의료인: 부서 medical team + 권한 staff 이상, 또는 admin (5일차 명세 1-2)
    # 환자 등록, 진료기록 등록에만 사용
    is_medical_staff = user.department == Department.MEDICAL and user.role == Role.STAFF
    if not (is_medical_staff or user.role == Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return user


# 의료인 전용 API에서 사용
CurrentMedicalStaff = Annotated[User, Depends(get_current_medical_staff)]
