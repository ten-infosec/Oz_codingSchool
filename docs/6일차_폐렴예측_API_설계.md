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

<!--
REQ-PRED-001 참고. 5일차 명세 형식(2-1 개요 / 2-2 요청 / 2-3 응답 / 2-4 비고)
- POST /api/v1/medical-records/{record_id}/predict, 스태프 이상, 본문 없음
- 새로 예측 201 / 같은 진료기록 + 같은 모델 결과 재사용 200, 본문은 AnalysisResponse(1-5)
- 404 진료기록 없음, 404 X-ray 파일 없음, 500 모델 오류
-->

---

## 3. AI 예측 결과 목록 조회 API (담당: 김민준)

### 3.1. API 개요 — REQ-PRED-002

| 항목 | 내용 |
| --- | --- |
| 요구사항 ID | REQ-PRED-002 |
| Method | `GET` |
| URL | `/api/v1/medical-records/{record_id}/analyses` |
| 기능 | 특정 진료기록에 저장된 AI 예측 결과 목록 조회 |
| 접근 권한 | Bearer Access Token 인증, `STAFF` 또는 `ADMIN` |
| 부서 제한 | 없음 (스태프 이상이면 부서와 관계없이 접근 가능) |
| Path Parameter | `record_id`: integer, 1 이상의 양의 정수, 필수 |
| Request Body | 없음 |
| 성공 응답 | `200 OK`, JSON 배열 |
| 정렬 기준 | `created_at DESC`, 동일 시각에는 `id DESC` |
| 성능 요구사항 | NFR-PRED-002: API 응답시간 3초 이내 |

본 API는 진료기록에 저장된 AI 폐렴 예측 결과를 조회하는 기능이다. 기존 분석 결과를 반환하며, 조회 과정에서 AI 모델을 다시 실행하지 않는다.

### 3.2. 요청 명세

**HTTP Request**

`GET /api/v1/medical-records/{record_id}/analyses`

**Path Parameter**

| 이름 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `record_id` | integer | Y | 조회할 진료기록의 고유 ID (1 이상) |

**Request Header**

| 이름 | 값 | 설명 |
| --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | 사용자 인증 토큰 |

Request Body는 사용하지 않는다.

### 3.3. 성공 응답 — 200 OK

**응답 예시**

```json
[
  {
    "id": 21,
    "record_id": 5,
    "is_pneumonia": true,
    "confidence": 97.68,
    "heatmap_url": "/media/heatmaps/example.png",
    "ai_model": "resnet18-E1b",
    "created_at": "2026-10-28T15:20:00"
  }
]
```

위 응답은 형식을 설명하기 위한 예시이며, 실제 값은 데이터베이스에 저장된 분석 결과에 따라 달라진다.

**응답 필드 정의**

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | integer | AI 분석 결과 고유 ID |
| `record_id` | integer | 해당 분석 결과가 속한 진료기록 ID |
| `is_pneumonia` | boolean | 폐렴 예측 여부 (`true`: 폐렴, `false`: 정상) |
| `confidence` | number | 예측 신뢰도, 백분율 0.00~100.00 (%) |
| `heatmap_url` | string/null | Grad-CAM 히트맵 파일 URL. 없는 경우 `null` |
| `ai_model` | string | 예측에 사용된 AI 모델 식별자 |
| `created_at` | string (date-time) | AI 예측 결과 생성 일시 |

**분석 결과가 없는 경우**

진료기록은 존재하지만 저장된 AI 분석 결과가 없는 경우 `200 OK`와 빈 배열을 반환한다.

```json
[]
```

### 3.4. 오류 응답

| HTTP 상태 코드 | 발생 조건 | 처리 내용 |
| --- | --- | --- |
| `401 Unauthorized` | 인증 토큰이 없거나 유효하지 않은 경우 | 인증 오류 반환 |
| `403 Forbidden` | `PENDING` 등 접근 권한이 없는 경우 | 접근 거부 |
| `404 Not Found` | 요청한 `record_id`에 해당하는 진료기록이 존재하지 않는 경우 | 진료기록 없음 반환 |
| `422 Unprocessable Entity` | `record_id`가 정수가 아니거나 1 미만인 경우 | 요청 파라미터 검증 오류 반환 |

### 3.5. 처리 흐름

1. 클라이언트가 진료기록 ID를 포함하여 GET 요청을 전송한다.
2. Access Token을 검증하고 사용자의 접근 권한을 확인한다.
3. 해당 ID의 진료기록이 존재하는지 확인한다.
4. 진료기록이 없으면 404 오류를 반환한다.
5. 진료기록이 존재하면 `ai_analysis_results` 테이블에서 해당 `record_id`의 분석 결과를 조회한다.
6. `created_at`을 기준으로 최신순 정렬하고, 동일한 시각에는 `id`를 기준으로 내림차순 정렬한다.
7. 조회한 결과를 JSON 배열로 반환한다.
8. 저장된 분석 결과가 없다면 빈 배열 `[]`을 반환한다.

### 3.6. 구현 및 성능 요구사항

- AI 분석 결과 목록은 데이터베이스에 저장된 데이터를 기준으로 반환한다.
- 조회 시 AI 모델 추론을 다시 실행하지 않는다.
- 새로운 AI 분석 결과를 생성하거나 기존 데이터를 수정하지 않는다.
- 인증 및 권한 검사는 기존 프로젝트의 공통 인증 체계를 사용한다.
- `STAFF`, `ADMIN` 권한을 가진 사용자만 접근할 수 있다.
- 응답시간은 NFR-PRED-002에 따라 3초 이내를 목표로 한다.
- 반환되는 `confidence`의 단위는 예측 실행 API와 동일한 백분율(0~100)로 통일한다.
- `heatmap_url`이 없는 경우 API 응답에서는 `null`을 허용한다.
- 실제 응답 필드 및 자료형은 팀 공통 응답 스키마와 일치해야 한다.

### 3.7. 검증 항목

| 테스트 항목 | 기대 결과 |
| --- | --- |
| 정상 권한으로 존재하는 진료기록 조회 | 200 OK 및 분석 결과 배열 |
| 분석 결과가 없는 진료기록 조회 | 200 OK 및 `[]` |
| 존재하지 않는 진료기록 조회 | 404 Not Found |
| 인증 토큰 없이 요청 | 401 Unauthorized |
| `PENDING` 권한으로 요청 | 403 Forbidden |
| 잘못된 `record_id` 요청 | 422 Unprocessable Entity |
| 분석 결과 여러 건 조회 | 생성 일시 기준 최신순 정렬 |
| 저장된 결과 조회 후 DB 확인 | 데이터 변경 없음 |
| API 응답시간 측정 | 3초 이내 |

※ 최종 테스트 결과는 실제 DB 및 팀 공통 API 구현과 연동하여 확인한다.