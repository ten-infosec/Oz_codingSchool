import enum


# SQLAlchemy Enum은 DB에 "이름"(M, F, PENDING ...)을 저장한다.
# 값("male", "pending" ...)은 API로 주고받을 때 쓰이며, 템플릿 화면(static/) 표기에 맞춘다.
# → 이름을 바꾸면 DB 마이그레이션이 필요하므로 이름은 바꾸지 않는다.


class Gender(str, enum.Enum):
    M = "male"
    F = "female"


class Role(str, enum.Enum):
    PENDING = "pending"  # 권한 부여 대기
    STAFF = "staff"      # 폐렴 추적 관련 데이터 CRUD 허용
    ADMIN = "admin"      # 전체 데이터 CRUD 허용


class Department(str, enum.Enum):
    MEDICAL = "medical team"  # 의료진
    DEV = "developer"         # 개발팀
    RESEARCH = "researcher"   # 연구진
