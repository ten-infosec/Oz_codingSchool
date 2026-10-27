from pydantic import BaseModel

from app.schemas.user import UserResponse


# ===== Auth Schemas (담당: 엄태은) =====


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # 액세스 토큰 만료까지 남은 시간(초)
    expires_in: int


class LoginResponse(TokenResponse):
    user: UserResponse
