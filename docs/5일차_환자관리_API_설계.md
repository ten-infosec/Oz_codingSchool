# 5일차 환자 관리 및 진료기록 API 설계

> 요구사항 정의서: 5일차 - 진료기록 사용자 요구사항 정의서 (REQ-PTNT-001 ~ 005, REQ-MDR-001 ~ 003, NFR-PTNT-001, NFR-MDR-001)
>
> 팀원별 담당
> - 엄태은: 공통 규칙, 환자 정보 수정, 진료기록 등록, 진료기록 목록 조회, 진료기록 상세 조회
>   (환자 정보 수정·진료기록 목록 조회는 김민준님 결석으로 대신 담당)
> - 장성은: 환자 정보 등록, 환자 정보 삭제
> - 여현지: 환자 목록 조회, 환자 정보 상세 조회
>
> 주소·칸 이름·값은 템플릿 화면(`static/apis.js`, `static/pages.js`, `static/templates/`)이 호출하는 방식에 맞춘다.

---

## 0. API 목록

| # | 기능 | 메서드 | 엔드포인트 | 권한 | 요구사항 | 담당 |
|---|---|---|---|---|---|---|
| 1 | 환자 정보 등록 | POST | `/api/v1/patients` | 의료인 | REQ-PTNT-001 | 장성은 |
| 2 | 환자 목록 조회 | GET | `/api/v1/patients` | 스태프 이상 | REQ-PTNT-002 | 여현지 |
| 3 | 환자 정보 상세 조회 | GET | `/api/v1/patients/{patient_id}` | 스태프 이상 | REQ-PTNT-003 | 여현지 |
| 4 | 환자 정보 수정 | PATCH | `/api/v1/patients/{patient_id}` | 스태프 이상 | REQ-PTNT-004 | 엄태은 |
| 5 | 환자 정보 삭제 | DELETE | `/api/v1/patients/{patient_id}` | 스태프 이상 | REQ-PTNT-005 | 장성은 |
| 6 | 진료기록 등록 | POST | `/api/v1/medical-records` | 의료인 | REQ-MDR-001 | 엄태은 |
| 7 | 진료기록 목록 조회 | GET | `/api/v1/patients/{patient_id}/medical-records` | 스태프 이상 | REQ-MDR-002 | 엄태은 |
| 8 | 진료기록 상세 조회 | GET | `/api/v1/medical-records/{record_id}` | 스태프 이상 | REQ-MDR-003 | 엄태은 |

---

## 1. 공통 규칙 (담당: 엄태은)

### 1-1. 기본 주소와 인증

- 모든 API는 `/api/v1`으로 시작한다.
- 모든 API는 로그인이 필요하다. 요청 헤더에 4일차 로그인 API로 받은 액세스 토큰을 담는다.

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

### 1-2. 권한

| 권한 표기 | 허용 대상 | 근거 |
|---|---|---|
| 스태프 이상 | 권한이 `staff` 또는 `admin`인 사용자 | 4일차 규칙: `pending`(대기자)은 마이페이지 외 모든 서비스 접근 불가 |
| 의료인 | 부서가 `medical team`이고 권한이 `staff` 이상인 사용자, 또는 `admin` | REQ-PTNT-001, REQ-MDR-001: "사내 의료인 역할을 가진 유저" |

- 환자 등록(1번)과 진료기록 등록(6번)만 **의료인** 권한이 필요하다.
- 나머지는 요구사항에 "사내 개발진, 의료 실무진, 연구진"으로 되어 있어 **스태프 이상**이면 부서와 관계없이 허용한다.

### 1-3. 공통 값 형식

| 항목 | 형식 | 비고 |
|---|---|---|
| 환자 이름 | 1~30자 | DB `patients.name` 길이 |
| 나이 | 정수 0~150 | |
| 성별 | `male`, `female` | 등록 시 필수 (REQ-PTNT-001). DB에는 `M`, `F`로 저장 |
| 연락처 (`phone_number`) | 숫자만 10~11자리 (예: `01012345678`) | 4일차 휴대폰 번호 형식과 동일. DB 칸 이름은 `phone` |
| 진료 차트 넘버 | 1~50자 | 중복 불가 (DB unique) |
| 증상 | 1자 이상 | |
| 날짜·시간 | ISO 8601 (예: `2026-10-27T15:30:00`) | |

### 1-4. 공통 환자 응답 객체 (`PatientResponse`)

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678",
  "created_at": "2026-10-27T15:30:00",
  "updated_at": "2026-10-27T15:30:00"
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 환자 고유 ID |
| name | string | 이름 |
| age | integer | 나이 |
| gender | string | 성별 (`male`, `female`) |
| phone_number | string | 연락처 (DB `patients.phone`) |
| created_at | string | 생성일시 |
| updated_at | string | 수정일시 |

### 1-5. X-ray 이미지 저장 규칙 (REQ-MDR-001 비고)

- 이미지는 **서버가 실행되는 컴퓨터의 로컬 저장소** `media/xray/` 폴더에 저장한다.
- 파일 이름은 원래 이름을 쓰지 않고 **서버가 새로 만든 랜덤 이름**(UUID)으로 저장한다. 같은 이름 덮어쓰기와 경로 조작(`../`)을 막기 위해서다.
- 허용 형식: `image/jpeg`, `image/png` / 최대 크기: 10MB
- DB `xray_images.image_url`에는 `/media/xray/<파일이름>` 경로를 저장하고, 응답에서는 화면에 맞춰 `xray_image_url` 칸으로 돌려준다. `app/main.py`가 `/media`를 `media` 폴더에 연결(mount)해 두었으므로 이 경로로 바로 이미지를 볼 수 있다.
- `media/` 폴더는 환자 의료 이미지가 쌓이는 곳이므로 Git에 올리지 않는다. (`.gitignore`에 추가)

### 1-6. 공통 에러 응답

| 상태 코드 | 상황 | 예시 |
|---|---|---|
| 401 Unauthorized | 토큰이 없거나, 만료되었거나, 위조된 경우 | `{"detail": "인증 정보가 유효하지 않습니다."}` |
| 403 Forbidden | 권한이 부족한 경우 (대기자, 의료인이 아닌 사용자의 등록 시도) | `{"detail": "접근 권한이 없습니다."}` |
| 404 Not Found | 환자 또는 진료기록이 없는 경우 | `{"detail": "환자를 찾을 수 없습니다."}` |
| 409 Conflict | 진료 차트 넘버가 이미 있는 경우 | `{"detail": "이미 사용 중인 차트 넘버입니다."}` |
| 422 Unprocessable Entity | 필수 값 누락, 형식 오류 | FastAPI 기본 검증 오류 형식 |

### 1-7. 성능 (NFR-PTNT-001, NFR-MDR-001)

- 모든 API는 3초 이내에 응답한다.

---

## 2. 환자 정보 등록 (담당: 장성은)

<!--
REQ-PTNT-001 참고. 4일차 회원가입 명세 형식 참고
- 권한: 의료인 (1-2)
- 본문: 이름, 나이, 성별, 연락처 (모두 필수, 1-3 형식)
- 성공: 201 Created + PatientResponse (1-4)
- 실패: 401, 403, 422
-->

---

## 3. 환자 목록 조회 (담당: 여현지)

### 3-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 환자 목록 조회 API |
| 설명 | 로그인한 사내 개발진, 의료 실무진, 연구진이 환자 관리 메뉴에서 의료진이 등록한 환자 목록을 조회한다. 이름으로 검색하고, 성별과 나이 범위로 필터링할 수 있다. |
| 엔드포인트 | `/api/v1/patients` |
| 메서드 | `GET` |
| 인증 필요 여부 | Y (스태프 이상) |
| 요구사항 | REQ-PTNT-002 |

### 3-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

**경로 파라미터**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 경로 파라미터를 사용하지 않음 |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 요청 본문을 사용하지 않음 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| name | string | N | 이름 검색어. 이름에 포함된 경우 조회 (부분 일치) |
| gender | string | N | 성별 필터. `male`(남), `female`(여). 미입력 시 전체 성별 |
| min_age | integer | N | 나이 범위의 최소값 (이상, 0~150). 미입력 시 하한 없음 |
| max_age | integer | N | 나이 범위의 최대값 (이하, 0~150). 미입력 시 상한 없음 |

**요청 예시**

```
GET /api/v1/patients?name=홍길동&gender=male&min_age=40&max_age=49
```

### 3-3. 응답(Response)

**성공: 200 OK**

```json
[
  {
    "id": 1,
    "name": "홍길동",
    "age": 45,
    "gender": "male",
    "phone_number": "01012345678",
    "created_at": "2026-10-27T15:30:00",
    "updated_at": "2026-10-27T15:30:00"
  }
]
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| [] | array | 환자 목록 (`PatientResponse`, 1-4 참고) |
| [].id | integer | 환자 고유 ID |
| [].name | string | 이름 |
| [].age | integer | 나이 |
| [].gender | string | 성별 (`male`, `female`) |
| [].phone_number | string | 연락처 |
| [].created_at | string | 생성일시 |
| [].updated_at | string | 수정일시 |

검색 결과가 없는 경우에도 200 OK와 함께 빈 배열을 돌려준다.

```json
[]
```

**실패**

- 401 Unauthorized: 토큰이 없거나 만료·변조된 경우

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

- 403 Forbidden: 권한이 `pending`(대기자)인 경우

```json
{
  "detail": "접근 권한이 없습니다."
}
```

- 422 Unprocessable Entity: `gender`가 `male`, `female`이 아니거나, `min_age`, `max_age`가 올바르지 않은 경우 (`min_age`가 `max_age`보다 큰 경우 포함, 1-6 참고)

### 3-4. 비고

- 스태프 이상(`staff`, `admin`) 권한이면 부서와 관계없이 호출할 수 있다. `pending` 권한은 403을 받는다. (1-2 참고)
- `name`은 이름만 검색한다. (부분 일치)
- `name`, `gender`, `min_age`, `max_age`를 함께 보내면 모든 조건을 만족하는 환자만 조회한다. (AND 조건)
- `min_age`, `max_age`는 둘 중 하나만 보내도 된다. 두 값 모두 경계값을 포함한다. (이상, 이하)
- 프론트엔드가 응답을 배열로 받아 `patients.length`로 개수를 세므로, 페이지네이션 없이 조건에 맞는 환자 전체를 배열로 돌려준다.
- 정렬은 `id` 내림차순(최신 등록 순)이다.
- 목록의 상세보기 버튼은 `[].id`로 환자 정보 상세 조회(REQ-PTNT-003) API를 호출한다.
- 연락처 등 개인정보가 포함되므로 인증된 사용자에게만 응답한다.

---

## 4. 환자 정보 상세 조회 (담당: 여현지)

### 4-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 환자 정보 상세 조회 API |
| 설명 | 로그인한 사내 개발진, 의료 실무진, 연구진이 환자 관리 메뉴의 목록에서 상세보기 버튼을 눌러 특정 환자의 정보를 확인한다. |
| 엔드포인트 | `/api/v1/patients/{patient_id}` |
| 메서드 | `GET` |
| 인증 필요 여부 | Y (스태프 이상) |
| 요구사항 | REQ-PTNT-003 |

### 4-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

**경로 파라미터**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| patient_id | integer | Y | 조회할 환자 고유 ID |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 요청 본문을 사용하지 않음 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

**요청 예시**

```
GET /api/v1/patients/1
```

### 4-3. 응답(Response)

**성공: 200 OK**

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 45,
  "gender": "male",
  "phone_number": "01012345678",
  "created_at": "2026-10-27T15:30:00",
  "updated_at": "2026-10-27T15:30:00"
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 환자 고유 ID |
| name | string | 이름 |
| age | integer | 나이 |
| gender | string | 성별 (`male`, `female`) |
| phone_number | string | 연락처 |
| created_at | string | 생성일시 |
| updated_at | string | 수정일시 |

**실패**

- 401 Unauthorized: 토큰이 없거나 만료·변조된 경우

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

- 403 Forbidden: 권한이 `pending`(대기자)인 경우

```json
{
  "detail": "접근 권한이 없습니다."
}
```

- 404 Not Found: 환자가 없는 경우

```json
{
  "detail": "환자를 찾을 수 없습니다."
}
```

- 422 Unprocessable Entity: `patient_id`가 정수가 아닌 경우 (1-6 참고)

### 4-4. 비고

- 스태프 이상(`staff`, `admin`) 권한이면 부서와 관계없이 호출할 수 있다. `pending` 권한은 403을 받는다. (1-2 참고)
- 요구사항의 확인 항목은 이름, 성별, 연락처, 나이이지만, 팀 공통 환자 응답 객체(`PatientResponse`, 1-4 참고)를 그대로 사용해 `id`, `created_at`, `updated_at`도 함께 돌려준다. 화면에서 필요 없는 필드는 프론트엔드에서 표시하지 않으면 된다.
- 연락처 등 개인정보가 포함되므로 인증된 사용자에게만 응답한다.

---

## 5. 환자 정보 수정 (담당: 엄태은)

<!--
REQ-PTNT-004 참고
- 권한: 스태프 이상
- 부분 수정(Partial): name, phone_number 중 보낸 항목만 수정 (화면은 두 칸을 함께 보냄)
- 둘 다 안 보낸 경우 처리 방법도 정해 주세요
- 없는 환자: 404
-->

---

## 6. 환자 정보 삭제 (담당: 장성은)

<!--
REQ-PTNT-005 참고
- 권한: 스태프 이상
- 환자를 삭제하면 진료기록, X-ray 이미지(DB 행 + media/xray/ 실제 파일)도 함께 영구 삭제
  (DB는 외래키 ON DELETE CASCADE로 자동 삭제되지만, 실제 이미지 파일은 코드에서 지워야 함)
- 성공: 204 No Content
- 없는 환자: 404
-->

---

## 7. 진료기록 등록 (담당: 엄태은)

### 7-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 진료기록 등록 API |
| 설명 | 의료인이 환자를 선택해 진료 차트 넘버, 증상, 흉부 X-ray 이미지를 함께 등록한다. |
| 엔드포인트 | `/api/v1/medical-records` |
| 메서드 | `POST` |
| 인증 필요 여부 | Y (의료인) |
| 요구사항 | REQ-MDR-001 |

### 7-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 액세스 토큰 |
| Content-Type | `multipart/form-data` | 글자 칸과 파일을 함께 보내는 형식 |

**본문 필드 (form-data)** · 화면(`pages.js handleRecordCreate`)이 보내는 이름 그대로

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| patient_id | integer | Y | 진료기록을 등록할 환자 고유 ID ("환자 정보를 검색하여 환자를 선택") |
| chart_number | string | Y | 진료 차트 넘버 (1~50자, 중복 불가) |
| symptoms | string | Y | 진료된 증상 |
| xray_image | file | Y | 흉부 X-ray 이미지 (`jpeg`, `png`, 최대 10MB) |
| shooting_datetime | string | N | X-ray 촬영 일시 (ISO 8601). 생략하면 업로드 시각으로 저장 |

**경로 파라미터 / 쿼리 파라미터**: 없음

### 7-3. 응답(Response)

**성공: 201 Created** (`MedicalRecordDetailResponse`)

```json
{
  "id": 10,
  "patient_id": 1,
  "chart_number": "CH-20261027-001",
  "symptoms": "3일 전부터 기침과 38도 발열, 호흡 시 흉통",
  "xray_image_url": "/media/xray/3f2b9c1e-8a4d-4f0e-9b7a-2c6d5e1f0a9b.png",
  "shooting_datetime": "2026-10-27T15:10:00",
  "created_at": "2026-10-27T15:30:00"
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 진료기록 ID |
| patient_id | integer | 환자 고유 ID |
| chart_number | string | 진료 차트 넘버 |
| symptoms | string | 증상 (전체) |
| xray_image_url | string \| null | 흉부 X-ray 이미지 주소. 서버 주소 뒤에 붙이면 바로 열림 (예: `http://127.0.0.1:8000/media/xray/...png`) |
| shooting_datetime | string \| null | X-ray 촬영 일시 |
| created_at | string | 생성일시 |

**실패**

- 401 Unauthorized: 토큰이 없거나 유효하지 않은 경우
- 403 Forbidden: 의료인이 아닌 경우

```json
{
  "detail": "접근 권한이 없습니다."
}
```

- 404 Not Found: `patient_id`에 해당하는 환자가 없는 경우

```json
{
  "detail": "환자를 찾을 수 없습니다."
}
```

- 409 Conflict: 차트 넘버가 이미 있는 경우

```json
{
  "detail": "이미 사용 중인 차트 넘버입니다."
}
```

- 415 Unsupported Media Type: 이미지가 `jpeg`, `png`가 아닌 경우

```json
{
  "detail": "jpeg 또는 png 이미지만 업로드할 수 있습니다."
}
```

- 413 Content Too Large: 이미지가 10MB를 넘는 경우

```json
{
  "detail": "이미지는 10MB 이하만 업로드할 수 있습니다."
}
```

- 422 Unprocessable Entity: 필수 값 누락, 형식 오류 (1-6 참고)

### 7-4. 비고

- 이미지 파일이 있으므로 요청 본문은 JSON이 아니라 `multipart/form-data`다. 같은 API에서 JSON 본문과 파일을 함께 받을 수 없다. (HTTP 규칙)
- 폼 칸을 Pydantic 모델(`Form()`)로 묶고 파일을 따로 받으면 FastAPI가 422(`body.form` missing)를 낸다. 칸마다 `Form()`으로 받거나, 파일까지 모델 안에 넣는다.
- 업로드한 이미지의 미리보기는 화면(프론트엔드)에서 처리한다. 서버는 저장 후 `xray_image_url`을 돌려준다.
- 저장 순서: 검증 → 파일 저장 → DB 저장. DB 저장이 실패하면 방금 저장한 파일을 지워 남는 파일이 없게 한다.
- 요구사항상 진료기록 1건에 이미지 1장이다. DB 구조(`xray_images.record_id`)는 여러 장을 허용하지만, 응답에는 첫 번째 이미지 주소만 `xray_image_url`로 돌려준다.

---

## 8. 진료기록 목록 조회 (담당: 엄태은)

<!--
REQ-MDR-002 참고
- 권한: 스태프 이상
- 경로 파라미터: patient_id (없는 환자: 404)
- 응답: **배열** [ {id, chart_number, symptoms, created_at} ] (화면이 records.map으로 사용)
- 증상: 100자 초과 시 앞 100자 + "…"
- 정렬 순서(최신순 등)도 정해 주세요
-->

---

## 9. 진료기록 상세 조회 (담당: 엄태은)

### 9-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 진료기록 상세 조회 API |
| 설명 | 진료기록 1건의 차트 넘버, 증상 전체, 흉부 X-ray 이미지를 조회한다. |
| 엔드포인트 | `/api/v1/medical-records/{record_id}` |
| 메서드 | `GET` |
| 인증 필요 여부 | Y (스태프 이상) |
| 요구사항 | REQ-MDR-003 |

### 9-2. 요청(Request)

**경로 파라미터**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| record_id | integer | Y | 진료기록 ID |

**본문 필드 / 쿼리 파라미터**: 없음

### 9-3. 응답(Response)

**성공: 200 OK**

- 7-3 진료기록 등록 성공 응답과 같은 형식 (`MedicalRecordDetailResponse`)
- 화면(`pages.js renderRecordDetail`)은 `xray_image_url`을 이미지 주소로, `patient_id`를 "환자로 돌아가기" 버튼에 사용한다.

**실패**

- 401 Unauthorized: 토큰이 없거나 유효하지 않은 경우
- 403 Forbidden: 대기자(`pending`)인 경우
- 404 Not Found: 진료기록이 없는 경우

```json
{
  "detail": "진료기록을 찾을 수 없습니다."
}
```

### 9-4. 비고

- 증상은 목록 조회(8번)와 달리 줄이지 않고 전체를 돌려준다.
- 환자 ID 없이 진료기록 ID만으로 조회한다. 진료기록 ID는 전체에서 하나뿐이라 환자 ID가 없어도 찾을 수 있기 때문이다.
