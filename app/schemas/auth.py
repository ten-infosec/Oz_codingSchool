from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse


# ===== Auth Schemas (담당: 엄태은) =====


class LoginRequest(BaseModel):
    email: EmailStr
    # 로그인은 형식 검사 없이 받는다 (규칙 위반 비밀번호도 "틀림"으로 처리하기 위해)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # 액세스 토큰 만료까지 남은 시간(초)
    expires_in: int


class LoginResponse(TokenResponse):
    user: UserResponse
