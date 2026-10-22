# app/apis/practice_apis.py
# Stage 2 - practice APIs (users CRUD with an in-memory list)

# re: 정규표현식(문자 패턴 검사) 도구. 이메일·비밀번호 형식을 검사할 때 쓴다
import re

# APIRouter: API들을 묶는 "작은 app" / HTTPException: 에러 응답(404, 400 등)을 보낼 때 쓴다
# status: 상태 코드를 숫자 대신 이름으로 쓰게 해 준다 (예: status.HTTP_404_NOT_FOUND)
from fastapi import APIRouter, HTTPException, status, Body, Path

# BaseModel: Request Body(요청 데이터)의 형식을 정의하는 틀
# Field: 각 항목의 제약 조건(최소·최대 길이, 최솟값 등)을 정한다
# field_validator: Field만으로 표현하기 어려운 검사(정규표현식 등)를 직접 함수로 작성할 때 쓴다
from pydantic import BaseModel, Field, field_validator


# ===== Router =====

# prefix: 이 라우터의 모든 경로 앞에 "/practice_api"가 자동으로 붙는다
# tags: Swagger(/docs)에서 API들을 "practice" 그룹으로 묶어서 보여준다
router = APIRouter(prefix="/practice_api", tags=["practice"])


# ===== Data (given) =====

# DB 대신 쓰는 임시 회원 목록 (서버를 껐다 켜면 처음 상태로 돌아간다)
user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!",
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!",
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@",
    },
]


# ===== Shared helpers =====

# 이메일 형식: "아이디@도메인.최상위도메인" (예: abc.def@example.co.kr)
# ^ 시작 / [\w.+-]+ 영문·숫자·_·.·+·- 1글자 이상 / @ / [\w-]+ 도메인 / (\.[\w-]+)+ ".com" 같은 부분 1번 이상 / $ 끝
EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

# 특수문자로 인정할 문자: 영문·숫자·공백이 아닌 모든 문자
SPECIAL_CHAR_PATTERN = re.compile(r"[^A-Za-z0-9\s]")

def check_email(value: str) -> str:
    # 정규표현식과 일치하지 않으면 ValueError를 던진다 → FastAPI가 자동으로 422 에러로 응답
    if not EMAIL_PATTERN.match(value):
        raise ValueError("올바른 이메일 형식이 아닙니다.")
    return value


def check_password(value: str) -> str:
    # re.search: 문자열 안에 패턴이 "하나라도" 있는지 찾는다
    if not re.search(r"[A-Z]", value):
        raise ValueError("비밀번호에 대문자가 1개 이상 필요합니다.")
    if not re.search(r"[a-z]", value):
        raise ValueError("비밀번호에 소문자가 1개 이상 필요합니다.")
    if not SPECIAL_CHAR_PATTERN.search(value):
        raise ValueError("비밀번호에 특수문자가 1개 이상 필요합니다.")
    return value


def to_public(user: dict) -> dict:
    # 응답에서 password를 빼고 id·name·age·email만 돌려준다 (비밀번호 노출 방지)
    return {key: user[key] for key in ("id", "name", "age", "email")}


def find_user_or_404(user_id: int) -> dict:
    # user_list를 앞에서부터 보면서 id가 같은 회원을 찾는다
    for user in user_list:
        if user["id"] == user_id:
            return user
    # 끝까지 못 찾으면 404 Not Found 응답
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"id가 {user_id}인 회원을 찾을 수 없습니다.",
    )


# ===== Schema: UserCreate (POST) =====

# TODO(김민준): 회원 추가용 UserCreate 작성 (name 2~10자, age 14 이상, email 최대 30자+정규식, password 8~20자+규칙)


# ===== Schema: UserUpdate (PATCH) =====

# TODO(여현지): 회원 수정용 UserUpdate 작성 (age, email, password 모두 선택 입력)

class UpdateUserRequest(BaseModel):
    age: int | None = Field(None, ge=14)    # 14세 이상
    email: str | None = Field(None, max_length=30)
    password: str | None = Field(None, min_length=8, max_length=20)

    # 이메일 검증 함수 연결
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None):
        if v is not None:
            return check_email(v)
        return v

    # 비밀번호 검증 함수 연결
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None):
        if v is not None:
            return check_password(v)
        return v

@router.patch(
        "/practice_api/users/{user_id}",
        summary="회원 정보 수정",
)
def update_user_handler(
    user_id: int = Path(..., ge=1),
    body: UpdateUserRequest = Body(...),
):

    # TODO(여현지): 회원 정보 수정 (입력된 항목만 반영, 아무것도 없으면 400)
    if body.age is None and body.email is None and body.password is None:
        raise HTTPException(
            status_code=400, detail="수정할 회원 정보를 하나 이상 입력해주세요."
        )
    # 회원정보 수정 로직
    for user in user_list:
        if user["id"] == user_id:
            if body.age:
                user["age"] = body.age
            if body.email:
                user["email"] = body.email
            if body.password:
                user["password"] = body.password
            return {"message": "회원 정보가 성공적으로 수정되었습니다.", "user": user}
    raise HTTPException(
        status_code=404, detail="해당하는 회원을 찾을 수 없습니다."
    )

# ===== API 1: GET /practice_api/users =====

@router.get("/users", summary="모든 회원 목록 조회")
def get_users():
    # 모든 회원을 password 없이 목록으로 돌려준다
    return [to_public(user) for user in user_list]


# ===== API 2: GET /practice_api/users/{user_id} =====

# TODO(장성은): 특정 회원 조회 (없으면 404)


# ===== API 3: POST /practice_api/users =====

# TODO(김민준): 회원 추가 (이메일 중복 불가, id 자동 증가)


# ===== API 4: PATCH /practice_api/users/{user_id} =====

# TODO(여현지): 회원 정보 수정 (입력된 항목만 반영, 아무것도 없으면 400) -> 회원 정보 수정 로직에 같이 작성해두었습니다.


# ===== API 5: DELETE /practice_api/users/{user_id} =====

# TODO(장성은): 회원 삭제 (없으면 404)
