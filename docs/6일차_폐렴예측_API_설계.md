# 6일차 AI 폐렴 예측 API 설계

> 요구사항 정의서: 6일차 - AI 폐렴 예측 사용자 요구사항 정의서 (REQ-PRED-001 ~ 002, NFR-PRED-001 ~ 002)
>
> 팀원별 담당
> - 엄태은: 공통 규칙, 사용 모델, 모델 코드(`worker/model.py`)
> - 여현지: 공통 예측 결과 응답 객체, 공통 에러 응답
> - 장성은: AI 폐렴 예측
> - 김민준: AI 예측 결과 목록 조회
>
> 주소·칸 이름은 템플릿 화면(`static/apis.js`, `static/pages.js`)이 호출하는 방식에 맞춘다.

---

## 0. API 목록

- `#` 번호는 아래 본문 섹션 번호와 같다. (1번은 공통 규칙)

| # | 기능 | 메서드 | 엔드포인트 | 권한 | 요구사항 | 담당 |
|---|---|---|---|---|---|---|
| 1 | 공통 규칙 | - | - | - | NFR-PRED-001, NFR-PRED-002 | 엄태은, 여현지 |
| 2 | AI 폐렴 예측 | POST | `/api/v1/medical-records/{record_id}/predict` | 스태프 이상 | REQ-PRED-001 | 장성은 |
| 3 | AI 예측 결과 목록 조회 | GET | `/api/v1/medical-records/{record_id}/analyses` | 스태프 이상 | REQ-PRED-002 | 김민준 |

---

## 1. 공통 규칙

### 1-1. 기본 주소와 인증 (담당: 엄태은)

- 모든 API는 `/api/v1`으로 시작하고, 로그인이 필요하다. 요청 헤더에 4일차 로그인 API로 받은 액세스 토큰을 담는다.

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

### 1-2. 권한 (담당: 엄태은)

| 권한 표기 | 허용 대상 | 근거 |
|---|---|---|
| 스태프 이상 | 권한이 `staff` 또는 `admin`인 사용자 (부서 무관) | REQ-PRED-001, 002: "사내 의료인, 개발팀, 연구자 권한을 가진 유저" |

- 의료인·개발팀·연구자 모두 사용할 수 있으므로 부서는 따지지 않는다. `pending`(대기자)은 403을 받는다.

### 1-3. 사용 모델 (NFR-PRED-001, 담당: 엄태은)

| 항목 | 내용 |
|---|---|
| 모델 이름 (`ai_model`) | `resnet18_e1b` |
| 구조 | ImageNet 사전학습 ResNet18, 전체 층 미세조정, 분류층 2클래스(0 정상, 1 폐렴) |
| 학습 데이터 | DACON 흉부 X-ray 폐렴 분류 데이터 (소아 흉부 X-ray) |
| 모델 파일 | `worker/models/final_resnet18.pth` (가중치만 저장한 state_dict, 44.8MB) |
| 전처리 | 224×224 크기 조정 → 흑백을 3채널로 복사 → ImageNet 평균·표준편차 정규화 |
| 판정 기준 | 폐렴 확률 ≥ 0.5이면 폐렴 |
| 학습 코드 | https://github.com/ten-infosec/dacon-chest-xray-pneumonia |

**평가 결과 (검증 데이터 1,044장 = 학습 데이터를 클래스 비율 유지해 20% 분할)**

| 지표 | 기준 (NFR-PRED-001) | 결과 | 판정 |
|---|---|---|---|
| Recall (민감도) = TP / (TP + FN) | ≥ 0.90 | 0.9768 | 충족 |
| Accuracy = (TP + TN) / 전체 | ≥ 0.80 | 0.9799 (리더보드 0.9407) | 충족 |
| FN (폐렴을 정상으로 오진) | 가장 위험 | 18건 | |
| FP (정상을 폐렴으로 오진) | | 3건 | |

- 학습 데이터가 소아 흉부 X-ray이므로, 성인 X-ray에서는 확신도가 낮게 나올 수 있다. 실제 서비스에서는 대상 환자군 데이터로 다시 학습·검증해야 한다.

### 1-4. 모델 실행 방식 (NFR-PRED-002, 담당: 엄태은)

- 서버가 켜질 때(`app/main.py` lifespan) 모델을 **한 번만** 메모리에 올리고, 모든 요청이 같은 모델을 재사용한다. 요청마다 모델 파일을 열면 3초 안에 응답할 수 없기 때문이다.
- 모델 파일은 `torch.load(..., map_location="cpu", weights_only=True)`로 불러온다. GPU에서 저장된 파일을 CPU에서 열고, 파일 안의 숨은 코드는 실행하지 않기 위해서다.
- 예측은 계산이 무거운 동기 함수이므로 `run_in_threadpool`로 별도 스레드에서 실행해, 예측하는 동안 다른 요청이 막히지 않게 한다.
- 로컬 측정(CPU): 첫 예측 0.69초(모델 로딩 포함), 이후 1장당 0.14초.
- 히트맵: Grad-CAM(마지막 합성곱 묶음 `layer4` 기준)으로 모델이 판단에 사용한 위치를 색으로 표시해 `media/heatmaps/`에 랜덤 파일 이름(UUID)으로 저장한다. `media/`는 Git에 올리지 않는다.

### 1-5. 공통 예측 결과 응답 객체 (`AnalysisResponse`, 담당: 여현지)

<!--
- 칸: id, record_id, is_pneumonia, confidence, heatmap_url, ai_model, created_at
- confidence 단위(%)와 소수 자리, DB Decimal → 응답 number 설명
- 화면(pages.js renderRecordDetail)이 쓰는 칸 표시
-->

### 1-6. 공통 에러 응답 (담당: 여현지)

<!--
- 401, 403(대기자), 404(진료기록 없음 / X-ray 파일 없음), 422, 500(모델 오류)
- 메시지는 팀 약속(정리 페이지) 문장 그대로
-->

---

## 2. AI 폐렴 예측 (담당: 장성은)

### 2-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | AI 폐렴 예측 API |
| 설명 | 진료기록 상세 화면에서 `AI 예측 결과보기`를 누르면, 진료기록 등록 때 업로드한 X-ray로 폐렴을 예측해 결과를 돌려준다. 같은 진료기록을 같은 모델로 이미 예측했다면 다시 추론하지 않고 저장된 결과를 돌려준다. |
| 엔드포인트 | `/api/v1/medical-records/{record_id}/predict` |
| 메서드 | `POST` |
| 인증 필요 여부 | Y (스태프 이상) |
| 요구사항 | REQ-PRED-001 |

### 2-2. 요청(Request)

**경로 파라미터**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | integer | Y | 예측할 진료기록 ID |

**본문 필드 / 쿼리 파라미터**: 없음 (이미지는 진료기록에 저장된 X-ray를 사용)

### 2-3. 응답(Response)

**성공: 201 Created** (새로 예측한 경우) / **200 OK** (저장된 결과를 재사용한 경우)

- 본문은 두 경우 모두 `AnalysisResponse`(1-5)와 같다.

```json
{
  "id": 1,
  "record_id": 10,
  "is_pneumonia": true,
  "confidence": 97.35,
  "heatmap_url": "/media/heatmaps/3f2b9c1e-8a4d-4f0e-9b7a-2c6d5e1f0a9b.png",
  "ai_model": "resnet18_e1b",
  "created_at": "2026-10-28T15:30:00"
}
```

**실패**

- 401 Unauthorized, 403 Forbidden (1-6 참고)
- 404 Not Found: 진료기록이 없는 경우 `{"detail": "진료기록을 찾을 수 없습니다."}`
- 404 Not Found: X-ray 파일이 없는 경우 `{"detail": "X-ray 이미지를 찾을 수 없습니다."}`
- 500 Internal Server Error: 모델 예측 중 오류 `{"detail": "AI 예측 중 오류가 발생했습니다."}`

### 2-4. 비고

- 처리 순서: 진료기록 확인(404) → 같은 `record_id` + 같은 `ai_model` 결과 조회 → 있으면 200으로 그대로 응답 → 없으면 X-ray 파일 경로 확인 → 예측 → DB 저장 → 201 응답.
- "같은 모델"은 `ai_model` 값(`resnet18_e1b`)으로 판단한다. 모델을 바꾸면 새 이름으로 다시 예측할 수 있다.
- DB 저장이 실패하면 방금 만든 히트맵 파일을 지워 남는 파일이 없게 한다.
- 새로 만든 결과와 재사용한 결과를 구분할 수 있도록 상태 코드를 다르게 했다. 화면은 두 경우 모두 성공으로 처리한다.

---

## 3. AI 예측 결과 목록 조회 (담당: 김민준)

<!--
REQ-PRED-002 참고. 5일차 명세 형식(3-1 ~ 3-4)
- GET /api/v1/medical-records/{record_id}/analyses, 스태프 이상
- 200 배열 (AnalysisResponse 목록, id 내림차순), 결과 없으면 []
- 404 진료기록 없음
-->
