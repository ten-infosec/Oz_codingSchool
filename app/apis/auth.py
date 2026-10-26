from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.core.config import settings
from app.core.dependencies import DbSession
from app.core.security import (
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    create_access_token,
    create_refresh_token,
)
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service


# ===== Router (담당: 엄태은) =====


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# 액세스 토큰 만료까지 남은 시간(초) = 30분 × 60
ACCESS_TOKEN_EXPIRES_IN = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        # 7일(초)
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        # 자바스크립트에서 읽을 수 없게 (NFR-USER-001)
        httponly=True,
        # 다른 사이트에서 보내는 요청에는 쿠키를 싣지 않게
        samesite="lax",
        # 인증 API를 호출할 때만 쿠키가 전송되게
        path=REFRESH_COOKIE_PATH,
        # 운영(HTTPS)에서는 True로 바꾼다
        secure=False,
    )


# ===== POST /api/v1/auth/login =====


@router.post(
    "/login",
    summary="로그인",
    response_model=LoginResponse,
)
async def login(body: LoginRequest, response: Response, db: DbSession):
    user = await auth_service.authenticate(db, body.email, body.password)

    # 리프레시 토큰은 쿠키로, 액세스 토큰은 응답 본문으로
    _set_refresh_cookie(response, create_refresh_token(user.id))

    return LoginResponse(
        access_token=create_access_token(user.id),
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
        user=UserResponse.model_validate(user),
    )


# ===== POST /api/v1/auth/token/refresh =====


@router.post(
    "/token/refresh",
    summary="액세스 토큰 재발급",
    response_model=TokenResponse,
)
async def refresh_access_token(
    db: DbSession,
    # 쿠키 이름이 refresh_token인 값을 읽는다 (없으면 None)
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    user = await auth_service.get_user_from_refresh_token(db, refresh_token)

    return TokenResponse(
        access_token=create_access_token(user.id),
        expires_in=ACCESS_TOKEN_EXPIRES_IN,
    )


# ===== POST /api/v1/auth/logout =====


@router.post(
    "/logout",
    summary="로그아웃",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(response: Response):
    # 리프레시 토큰 쿠키 삭제 (설정할 때와 같은 path를 줘야 지워진다)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    # 204는 응답 본문이 없어야 하므로 아무것도 return하지 않는다
