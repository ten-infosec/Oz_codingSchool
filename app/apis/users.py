from fastapi import APIRouter, status

from app.core.dependencies import CurrentAdmin, CurrentUser, DbSession
from app.schemas.user import UserResponse
from app.services import user_service


router = APIRouter(prefix="/api/v1/users", tags=["users"])

# 사용 방법
# - 로그인 필요(권한 무관, PENDING 포함): current_user: CurrentUser
# - 관리자 전용:                          admin: CurrentAdmin
# - DB 세션:                              db: DbSession
# - 응답에 사용자 정보:                    response_model=UserResponse
# - DB 코드는 비동기 (async def, await)


# ===== Signup / Withdraw (담당: 장성은) =====
# POST   /api/v1/users/signup   회원가입  (status_code=201, 인증 없음)
# DELETE /api/v1/users/me       회원 탈퇴 (CurrentUser)


# ===== My Page (담당: 김민준) =====
# GET    /api/v1/users/me            마이페이지 조회 (CurrentUser)
# PATCH  /api/v1/users/me            회원 정보 수정  (CurrentUser)
# PATCH  /api/v1/users/me/password   비밀번호 변경   (CurrentUser)


# ===== Admin (담당: 여현지) =====
# GET    /api/v1/users                    회원 목록 조회 (CurrentAdmin)
# PATCH  /api/v1/users/{user_id}/role     회원 권한 변경 (CurrentAdmin)
