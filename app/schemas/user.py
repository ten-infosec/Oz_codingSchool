import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.models.enums import Department, Gender, Role


# ===== Common Validators (담당: 엄태은) =====
# 명세 1-4 공통 값 형식. 회원가입·정보 수정·비밀번호 변경에서 같이 쓴다.


_PASSWORD_SPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")
_PHONE_PATTERN = re.compile(r"^\d{10,11}$")


# 템플릿 화면(static/apis.js)이 이 문장을 그대로 찾아서 보여 주므로 글자 하나도 바꾸지 않는다
PASSWORD_RULE_MESSAGE = "비밀번호는 대소문자, 특수문자, 숫자를 각 1개씩 포함한 8자리 이상이어야 합니다."


def _check_password(value: str) -> str:
    # 8~64자, 영문 대문자·소문자·숫자·특수문자 각 1개 이상
    # (64자 상한: 너무 긴 비밀번호로 해싱에 시간을 쓰게 만드는 요청을 막기 위해)
    if not (
        8 <= len(value) <= 64
        and re.search(r"[A-Z]", value)
        and re.search(r"[a-z]", value)
        and re.search(r"\d", value)
        and _PASSWORD_SPECIAL.search(value)
    ):
        raise ValueError(PASSWORD_RULE_MESSAGE)
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
from pydantic import EmailStr


class SignupRequest(BaseModel):
    # 회원가입 요청 본문 (명세 2-2)
    email: Annotated[EmailStr, Field(max_length=255)]
    password: Password
    name: UserName
    department: Department
    gender: Gender
    phone_number: PhoneNumber
    # role은 받지 않는다 → 서버에서 PENDING으로 저장 (명세 2-4)


# ===== My Page (담당: 김민준) =====
# 민준님 명세(4일차 문서 8~10번) 기준으로 작성 (민준님 결석으로 태은 대신 작성)
from pydantic import model_validator


class UserUpdateRequest(BaseModel):
    # PATCH /api/v1/users/me 요청 본문 (보낸 항목만 수정)
    # extra="forbid": 이름·이메일·권한처럼 수정할 수 없는 항목을 보내면 422
    model_config = ConfigDict(extra="forbid")

    department: Department | None = None
    phone_number: PhoneNumber | None = None

    @model_validator(mode="after")
    def _at_least_one(self):
        # 변경 항목이 하나도 없으면 422 (명세 9번)
        if self.department is None and self.phone_number is None:
            raise ValueError("수정할 항목(부서, 휴대폰 번호)을 하나 이상 보내 주세요.")
        return self


class PasswordChangeRequest(BaseModel):
    # PATCH /api/v1/users/me/password 요청 본문 (템플릿 화면도 같은 이름으로 보냄)
    current_password: str
    new_password: Password


class MessageResponse(BaseModel):
    message: str



# ===== Admin (담당: 여현지) =====
# REQ-USER-004 회원 목록 조회, REQ-USER-005 회원 권한 변경
# 템플릿 화면(static/apis.js) 약속: GET /admin/users?query=&department= → 배열, PATCH /admin/users/role {user_id, new_role}


class UserListQuery(BaseModel):
    # GET /api/v1/admin/users 쿼리 파라미터
    query: str | None = Field(default=None, max_length=100)  # 이메일 또는 이름 검색
    department: Department | None = None  # 부서 필터 (미입력 시 전체)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=100, ge=1, le=100)


class RoleUpdateRequest(BaseModel):
    # PATCH /api/v1/admin/users/role 요청 본문
    user_id: int  # 권한을 변경할 회원 ID
    new_role: Role  # pending / staff / admin
