from datetime import datetime

from pydantic import BaseModel


# ===== Medical Record Schemas (담당: 엄태은) =====
# 진료기록 등록 요청은 파일이 있어 JSON 모델이 아니라 apis/medical_records.py에서 Form()으로 받는다


class MedicalRecordDetailResponse(BaseModel):
    # 진료기록 등록(6) 성공, 진료기록 상세(8) 응답 (명세 7-3)
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_image_url: str | None
    shooting_datetime: datetime | None
    created_at: datetime


class MedicalRecordListItem(BaseModel):
    # 진료기록 목록(7) 응답의 한 줄 (증상은 100자 넘으면 줄임)
    id: int
    chart_number: str
    symptoms: str
    created_at: datetime
