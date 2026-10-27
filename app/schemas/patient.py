from datetime import datetime
from typing import Annotated

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.enums import Gender
from app.schemas.user import PhoneNumber


# ===== Common (담당: 엄태은) =====
# 5일차 명세 1-3 공통 값 형식, 1-4 공통 환자 응답 객체


PatientName = Annotated[str, Field(min_length=1, max_length=30)]
Age = Annotated[int, Field(ge=0, le=150)]
# 연락처는 4일차 휴대폰 번호 검증(PhoneNumber)을 그대로 사용


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender | None
    # DB 칸 이름은 phone, 화면이 쓰는 이름은 phone_number → 읽을 때 phone에서 가져온다
    phone_number: str = Field(validation_alias=AliasChoices("phone", "phone_number"))
    created_at: datetime
    updated_at: datetime | None


# ===== Create (담당: 장성은) =====
# 예: class PatientCreateRequest(BaseModel): name: PatientName, age: Age, gender: Gender, phone_number: PhoneNumber


# ===== List (담당: 여현지) =====
# 예: class PatientListQuery(BaseModel): name, gender, min_age, max_age (명세 3번)


# ===== Update (담당: 엄태은, 김민준님 결석으로 대신 담당) =====


class PatientUpdateRequest(BaseModel):
    # PATCH /api/v1/patients/{patient_id} (보낸 항목만 수정)
    model_config = ConfigDict(extra="forbid")

    name: PatientName | None = None
    phone_number: PhoneNumber | None = None
