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
# 민준님 명세 기준 (민준님 결석으로 태은 대신 작성)
from app.schemas.user import PasswordChangeRequest, UserUpdateRequest


async def update_me(db: AsyncSession, user: User, body: UserUpdateRequest) -> User:
    # exclude_unset=True: 요청에 실제로 들어온 항목만 꺼낸다 (부분 수정)
    values = body.model_dump(exclude_unset=True)

    # 다른 회원이 이미 쓰는 휴대폰 번호면 409 (본인 번호 그대로 보낸 경우는 통과)
    new_phone = values.get("phone_number")
    if new_phone and new_phone != user.phone_number:
        if await user_repository.get_by_phone_number(db, new_phone) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 휴대폰 번호입니다.",
            )

    return await user_repository.update(db, user, values)


async def change_password(db: AsyncSession, user: User, body: PasswordChangeRequest) -> None:
    # 1) 현재 비밀번호 확인
    if user.hashed_password is None or not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다.",
        )
    # 2) 새 비밀번호는 기존과 달라야 한다
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.",
        )
    # 3) 해싱해서 저장
    await user_repository.update_password(db, user, hash_password(body.new_password))


# ===== Admin (담당: 여현지) =====
from app.schemas.user import RoleUpdateRequest, UserListQuery


async def get_users(db: AsyncSession, query: UserListQuery) -> list[User]:
    # 페이지 번호를 DB 조회용 offset으로 변환
    offset = (query.page - 1) * query.size
    return await user_repository.get_list(
        db,
        keyword=query.query,
        department=query.department,
        offset=offset,
        limit=query.size,
    )


async def update_role(db: AsyncSession, admin: User, body: RoleUpdateRequest) -> User:
    # 관리자 본인의 권한은 바꿀 수 없다 (관리자가 0명이 되는 상황 방지, 화면도 본인 행은 비활성화)
    if body.user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="본인의 권한은 변경할 수 없습니다.",
        )

    user = await user_repository.get_by_id(db, body.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return await user_repository.update_role(db, user, body.new_role)
