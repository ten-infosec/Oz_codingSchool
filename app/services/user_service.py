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
from app.schemas.user import (
    RoleUpdateRequest,
    RoleUpdateResponse,
    UserListQuery,
    UserListResponse,
    UserResponse,
)

async def get_users(db: AsyncSession, query: UserListQuery) -> UserListResponse:
    # 페이지 번호를 DB 조회용 offset으로 변환
    offset = (query.page - 1) * query.size

    users, total = await user_repository.get_list(
        db,
        keyword=query.keyword,
        department=query.department,
        offset=offset,
        limit=query.size,
    )

    return UserListResponse(
        total=total,
        page=query.page,
        size=query.size,
        items=[UserResponse.model_validate(user) for user in users],
    )


async def update_roles(db: AsyncSession, body: RoleUpdateRequest) -> RoleUpdateResponse:
    users = await user_repository.get_by_ids(db, body.user_ids)

    # 조회된 수가 요청한 수보다 적으면 존재하지 않는 ID가 섞여 있다는 뜻
    # (RoleUpdateRequest에서 중복 ID를 이미 제거했기 때문에 개수 비교가 정확하다)
    if len(users) != len(body.user_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자가 포함되어 있습니다.",
        )

    users = await user_repository.update_roles(db, users, body.role)
    await db.commit()   # TODO: 팀 commit 방식에 맞춰 조정

    return RoleUpdateResponse(
        updated_count=len(users),
        role=body.role,
        users=[UserResponse.model_validate(user) for user in users],
    )