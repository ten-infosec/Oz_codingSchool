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
# - 회원가입: 이메일·휴대폰 중복이면 409, 비밀번호는 hash_password로 저장, role은 Role.PENDING
# - 회원 탈퇴: DB에서 즉시 삭제


# ===== My Page (담당: 김민준) =====
# - 정보 수정: 보낸 값만 수정 (model_dump(exclude_unset=True)), 휴대폰 중복이면 409
# - 비밀번호 변경: verify_password로 기존 비밀번호 확인 후 hash_password로 저장


# ===== Admin (담당: 여현지) =====
# - 목록 조회: 이메일·이름 검색, 부서 필터
# - 권한 변경: 대상이 없으면 404
