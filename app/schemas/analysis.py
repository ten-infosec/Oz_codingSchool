from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ===== Analysis Response (담당: 여현지) =====
# AI 예측 실행(POST /predict)과 예측 결과 목록(GET /analyses)이 함께 쓰는 응답 형식 (6일차 명세 1-4)


class AnalysisResponse(BaseModel):
    # SQLAlchemy AIAnalysisResult 객체를 그대로 넘겨도 응답으로 바꿀 수 있게 하는 설정
    model_config = ConfigDict(from_attributes=True)

    # 예측 결과 고유 ID
    id: int
    # 어떤 진료기록의 예측인지
    record_id: int
    # 폐렴 여부 (True = 폐렴)
    is_pneumonia: bool
    # 판정한 쪽의 확률(%) — DB는 Decimal(5,2)이지만 화면에서 숫자로 쓰기 쉽게 float로 응답
    confidence: float
    # Grad-CAM 히트맵 주소 (/media/heatmaps/...)
    heatmap_url: str
    # 사용한 모델 이름
    ai_model: str
    # 예측 수행 일시 (화면 "수행 일시" 칸)
    created_at: datetime

# → DB의 예측 결과 한 줄을 화면이 쓰는 칸 이름(REQ-PRED-002 목록 항목) 그대로 응답하겠다