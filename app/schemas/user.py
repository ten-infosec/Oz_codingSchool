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
# 예: class UserListQuery(BaseModel): keyword: str | None = None, department: Department | None = None
#     class RoleUpdateRequest(BaseModel): role: Role
