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
from fastapi import Response

from app.core.security import REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from app.schemas.user import SignupRequest


# POST /api/v1/users/signup 회원가입 (명세 2번)
@router.post(
    "/signup",
    summary="회원가입",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def signup(body: SignupRequest, db: DbSession):
    return await user_service.signup(db, body)


# DELETE /api/v1/users/me 회원 탈퇴 (명세 11번)
@router.delete(
    "/me",
    summary="회원 탈퇴",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def withdraw(current_user: CurrentUser, response: Response, db: DbSession):
    await user_service.withdraw(db, current_user)
    # 리프레시 토큰 쿠키도 삭제 (로그아웃과 같은 path를 줘야 지워진다)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    # 204는 응답 본문이 없어야 하므로 아무것도 return하지 않는다


# ===== My Page (담당: 김민준) =====
# GET    /api/v1/users/me            마이페이지 조회 (CurrentUser)
# PATCH  /api/v1/users/me            회원 정보 수정  (CurrentUser)
# PATCH  /api/v1/users/me/password   비밀번호 변경   (CurrentUser)
# 민준님 명세(4일차 문서 8~10번) 기준 (민준님 결석으로 태은 대신 작성)
from app.schemas.user import MessageResponse, PasswordChangeRequest, UserUpdateRequest


@router.get("/me", summary="마이페이지 조회", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    # 로그인 확인(CurrentUser)에서 이미 DB 조회를 마쳤으므로 그대로 돌려준다
    # 템플릿 화면은 로그인 직후 이 API로 내 정보를 가져온다
    return current_user


@router.patch("/me", summary="회원 정보 수정", response_model=UserResponse)
async def update_me(current_user: CurrentUser, body: UserUpdateRequest, db: DbSession):
    return await user_service.update_me(db, current_user, body)


@router.patch("/me/password", summary="비밀번호 변경", response_model=MessageResponse)
async def change_password(current_user: CurrentUser, body: PasswordChangeRequest, db: DbSession):
    await user_service.change_password(db, current_user, body)
    return MessageResponse(message="비밀번호가 성공적으로 변경되었습니다.")


# ===== Admin (담당: 여현지) =====
# GET    /api/v1/admin/users          회원 목록 조회 (CurrentAdmin)
# PATCH  /api/v1/admin/users/role     회원 권한 변경 (CurrentAdmin)
# 템플릿 화면(static/apis.js)이 /admin/users 주소를 쓰므로 별도 라우터로 분리 (main.py에서 등록)
from typing import Annotated

from fastapi import Query

from app.schemas.user import RoleUpdateRequest, UserListQuery

admin_router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])


@admin_router.get(
    "",
    response_model=list[UserResponse],
    summary="회원 목록 조회",
)
async def get_users(
    admin: CurrentAdmin,
    db: DbSession,
    query: Annotated[UserListQuery, Query()],
):
    # 이메일/이름 검색(query) + 부서 필터(department)
    return await user_service.get_users(db, query)


@admin_router.patch(
    "/role",
    response_model=UserResponse,
    summary="회원 권한 변경",
)
async def update_user_role(
    admin: CurrentAdmin,
    db: DbSession,
    body: RoleUpdateRequest,
):
    return await user_service.update_role(db, admin, body)
