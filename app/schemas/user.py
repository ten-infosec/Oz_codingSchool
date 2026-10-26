import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models.enums import Department, Gender, Role


# ===== Common Validators (담당: 엄태은) =====
# 명세 1-4 공통 값 형식. 회원가입·정보 수정·비밀번호 변경에서 같이 쓴다.


_PASSWORD_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")
_PHONE_PATTERN = re.compile(r"^\d{10,11}$")


def _check_password(value: str) -> str:
    # 8~20자, 영문·숫자·특수문자 각 1개 이상
    if not 8 <= len(value) <= 20:
        raise ValueError("비밀번호는 8~20자여야 합니다.")
    if not re.search(r"[A-Za-z]", value):
        raise ValueError("비밀번호에 영문이 1개 이상 포함되어야 합니다.")
    if not re.search(r"\d", value):
        raise ValueError("비밀번호에 숫자가 1개 이상 포함되어야 합니다.")
    if not _PASSWORD_SPECIAL.search(value):
        raise ValueError("비밀번호에 특수문자가 1개 이상 포함되어야 합니다.")
    return value


def _check_phone_number(value: str) -> str:
    # 숫자만 10~11자리 (예: 01012345678)
    if not _PHONE_PATTERN.match(value):
        raise ValueError("휴대폰 번호는 숫자만 10~11자리로 입력해 주세요.")
    return value


# 필드 타입으로 바로 쓸 수 있는 검증 타입
# 예) password: Password / phone_number: PhoneNumber
Password = Annotated[str, AfterValidator(_check_password)]
PhoneNumber = Annotated[str, AfterValidator(_check_phone_number)]
UserName = Annotated[str, Field(min_length=1, max_length=20)]


# ===== Common Response (담당: 엄태은) =====
# 명세 1-5 공통 사용자 응답 객체. hashed_password는 절대 넣지 않는다.


class UserResponse(BaseModel):
    # SQLAlchemy User 객체를 그대로 넘겨도 응답으로 바꿀 수 있게 하는 설정
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: Role
    is_active: bool


# ===== Signup / Withdraw (담당: 장성은) =====
# 예: class SignupRequest(BaseModel): email: EmailStr, password: Password, name: UserName, ...


# ===== My Page (담당: 김민준) =====
# 예: class UserUpdateRequest(BaseModel): department: Department | None = None, phone_number: PhoneNumber | None = None
#     class PasswordChangeRequest(BaseModel): current_password: str, new_password: Password



# ===== Admin (담당: 여현지) =====
# REQ-USER-004 회원 목록 조회, REQ-USER-005 회원 권한 변경

from pydantic import field_validator

class UserListQuery(BaseModel):
    # GET /api/v1/users 쿼리 파라미터
    keyword: str | None = Field(default=None, max_length=100)  # 이메일 또는 이름 검색
    department: Department | None = None  # 부서 필터 (미입력 시 전체)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class UserListResponse(BaseModel):
    # GET /api/v1/users 응답
    total: int  # 검색·필터 조건에 해당하는 전체 회원 수
    page: int
    size: int
    items: list[UserResponse]


class RoleUpdateRequest(BaseModel):
    # PATCH /api/v1/users/role 요청 본문
    user_ids: list[int] = Field(min_length=1)  # 권한을 변경할 회원 ID 목록 (1개 이상)
    role: Role  # PENDING / STAFF / ADMIN

    @field_validator("user_ids")
    @classmethod
    def _remove_duplicate_ids(cls, value: list[int]) -> list[int]:
        # 같은 ID가 여러 번 들어와도 한 번만 처리 (순서는 유지)
        return list(dict.fromkeys(value))

class RoleUpdateResponse(BaseModel):
    # PATCH /api/v1/users/role 응답
    updated_count: int  # 권한이 변경된 회원 수
    role: Role  # 변경된 권한
    users: list[UserResponse]  # 권한이 변경된 회원 목록