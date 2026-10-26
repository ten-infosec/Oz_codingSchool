from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings


# ===== Password Hashing (argon2) =====


# argon2 해싱 도구 (기본 설정이 권장값이라 그대로 사용)
_password_hasher = PasswordHasher()


def hash_password(plain_password: str) -> str:
    # 평문 비밀번호 → 되돌릴 수 없는 해시 문자열
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # argon2는 비밀번호가 틀리면 False가 아니라 예외를 던진다
    # → 예외를 잡아서 False로 바꿔 줘야 500 에러가 나지 않는다
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        return False


# ===== JWT =====


TokenType = Literal["access", "refresh"]

# 리프레시 토큰을 담는 쿠키 이름과 경로 (인증 API에서만 쿠키가 전송되도록 경로 제한)
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _create_token(user_id: int, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        # sub(subject): 토큰 주인. JWT 규칙상 문자열로 넣는다 (NFR-USER-001: user_id만 저장)
        "sub": str(user_id),
        # 액세스/리프레시 구분 (액세스 토큰으로 재발급을 시도하는 것을 막기 위해)
        "type": token_type,
        # 발급 시각, 만료 시각
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: TokenType) -> int | None:
    # 토큰을 검증하고 user_id를 꺼낸다. 문제가 있으면 None
    # (만료, 서명 위조, 형식 오류, 종류 불일치 모두 None)
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None

    if payload.get("type") != expected_type:
        return None

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None
