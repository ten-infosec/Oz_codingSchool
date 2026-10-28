# 6일차 폐렴 예측 API 설계 — 김민준 담당분

> **공통 명세에 합칠 내용:** REQ-PRED-002(예측 결과 목록 조회). `main` ZIP에는 공통 `docs/6일차_폐렴예측_API_설계.md`가 아직 없어, 해당 파일을 새로 덮어쓰지 않고 **담당분만 별도 문서**로 작성함. 다른 팀원이 공통 명세를 만들었다면 아래 섹션만 편집·추가한다.

## REQ-PRED-002 — AI 예측 결과 목록 조회

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/v1/medical-records/{record_id}/analyses` |
| 기능 | 특정 진료기록에 저장된 AI 예측 결과 전체 조회 (추론 재실행 없음) |
| 접근 권한 | Bearer access token, `STAFF` 또는 `ADMIN` (부서 무관), `PENDING` 금지 |
| Path | `record_id`: 양의 정수(1 이상), 필수 |
| Request Body | 없음 |
| Success | `200 OK`, JSON 배열. 결과가 없으면 `[]` |
| 정렬 | `created_at DESC`, 동일 시각에는 `id DESC` |
| 성능 | NFR-PRED-002: 3초 이내. DB 조회만 수행, 추론하지 않음 |

### 200 OK — 응답 예시

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

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | integer | 분석 결과 고유 ID |
| `record_id` | integer | 대상 진료기록 ID |
| `is_pneumonia` | boolean | 폐렴 여부 |
| `confidence` | number | 백분율 0.00~100.00 (%) |
| `heatmap_url` | string/null | Grad-CAM 히트맵 URL. API 응답에서는 null 허용 |
| `ai_model` | string | 실제 추론에 사용한 모델 식별자 |
| `created_at` | string (date-time) | 예측 결과 생성 일시 |

### 오류 응답

| 코드 | 조건 |
| --- | --- |
| `401 Unauthorized` | 토큰 누락·위조·만료 등 인증 실패 |
| `403 Forbidden` | `PENDING`, 비활성 계정 또는 권한 부족 |
| `404 Not Found` | `record_id`에 해당하는 진료기록 없음 |
| `422 Unprocessable Entity` | 경로 매개변수가 양의 정수가 아님 |

### 구현 규칙

1. `CurrentStaff`를 적용해 STAFF/ADMIN만 허용한다.
2. 먼저 진료기록이 존재하는지 검사한다. 없다면 404를 반환한다.
3. 진료기록이 있으면 `ai_analysis_results`에서 `record_id`로 필터링하고 최신순으로 조회한다.
4. 저장된 결과만 읽으며 DB 쓰기·모델 추론·히트맵 생성은 수행하지 않는다.
5. 결과가 한 건도 없으면 빈 배열 `[]`을 200으로 반환한다.
6. UI `static/pages.js`가 `confidence` 뒤에 `%`를 붙이므로, **0~1 소수값이 아니라 0~100 백분율로 저장한 값을 그대로 반환**한다. `Numeric(5,2)` 컬럼의 소수점 두 자리 정밀도를 고려한다.

### 팀 합의가 필요한 사항

- 현행 SQLAlchemy 및 Alembic 스키마에서 `heatmap_url`은 `nullable=False`다. 요구사항의 '히트맵 선택'과 충돌하므로 **POST 구현자(장성은), 모델 담당자(엄태은), 스키마 담당자(여현지)**가 결정해야 한다. DB를 수정하지 않는다면 히트맵이 없는 결과에도 `""`(빈 문자열) 등을 일관되게 저장해야 한다. 이 GET API는 DB 변경을 하지 않는다.
- `confidence`는 해당 예측 모델의 무엇에 대한 확신인지(예측 클래스 확률 vs 폐렴 확률), 모델별 이름 및 0~100 단위를 POST와 GET에서 동일하게 정의해야 한다.
- 공통 응답 스키마가 추가되는 경우 이 문서와 `AIAnalysisListItem`의 필드명을 맞춘다.

### 검증 시나리오

- STAFF/ADMIN: 정상 진료기록 조회 → 200, 배열
- 미인증: 401 / PENDING: 403
- 없는 진료기록: 404
- 존재하는 진료기록·분석 결과 0건: 200, `[]`
- 분석 결과 2건 이상: 최신 `created_at`부터 정렬
- 조회 실행으로 `ai_analysis_results`에 새 행이 생기지 않음
- 실제 팀 MySQL/Swagger/브라우저에서 응답 3초 이하 확인
