# 4일차 User API 설계

> 요구사항 정의서: 4일차 - User 사용자 요구사항 정의서 (REQ-USER-001 ~ 009, NFR-USER-001 ~ 003)
>
> 팀원별 담당
> - 엄태은: 공통 규칙, 로그인, 토큰 재발급, 로그아웃
> - 장성은: 회원가입, 회원 탈퇴
> - 김민준: 마이페이지 조회, 회원 정보 수정, 비밀번호 변경
> - 여현지: 회원 목록 조회, 회원 권한 변경

---

## 0. API 목록

| # | 기능 | 메서드 | 엔드포인트 | 인증 | 권한 | 요구사항 | 담당 |
|---|---|---|---|---|---|---|---|
| 1 | 회원가입 | POST | `/api/v1/users/signup` | N | - | REQ-USER-001 | 장성은 |
| 2 | 로그인 | POST | `/api/v1/auth/login` | N | - | REQ-USER-002, NFR-USER-001 | 엄태은 |
| 3 | 토큰 재발급 | POST | `/api/v1/auth/token/refresh` | 쿠키 | - | NFR-USER-001 | 엄태은 |
| 4 | 로그아웃 | POST | `/api/v1/auth/logout` | N | - | REQ-USER-003 | 엄태은 |
| 5 | 회원 목록 조회 | GET | `/api/v1/users` | Y | ADMIN | REQ-USER-004 | 여현지 |
| 6 | 회원 권한 변경 | PATCH | `/api/v1/users/{user_id}/role` | Y | ADMIN | REQ-USER-005 | 여현지 |
| 7 | 마이페이지 조회 | GET | `/api/v1/users/me` | Y | 전체 | REQ-USER-006 | 김민준 |
| 8 | 회원 정보 수정 | PATCH | `/api/v1/users/me` | Y | 전체 | REQ-USER-007 | 김민준 |
| 9 | 비밀번호 변경 | PATCH | `/api/v1/users/me/password` | Y | 전체 | REQ-USER-008 | 김민준 |
| 10 | 회원 탈퇴 | DELETE | `/api/v1/users/me` | Y | 전체 | REQ-USER-009 | 장성은 |

---

## 1. 공통 규칙 (담당: 엄태은)

### 1-1. 기본 주소

- 모든 API는 `/api/v1`으로 시작한다.
- `app/main.py`의 `catch_all`이 `api/v1`로 시작하는 주소를 API 경로로 구분하기 때문이다.

### 1-2. 인증 방식 (NFR-USER-001)

| 구분 | 액세스 토큰 | 리프레시 토큰 |
|---|---|---|
| 용도 | API 인가 | 액세스 토큰 재발급 |
| 만료 | 30분 | 7일 |
| 전달 방식 | 응답 본문 → 요청 헤더 `Authorization: Bearer <토큰>` | `HttpOnly` 쿠키 (`refresh_token`) |
| 페이로드 | `user_id`(`sub`), 만료 시각(`exp`), 토큰 종류(`type`) | 동일 |

- 인증이 필요한 API는 요청 헤더에 아래 값을 담아 보낸다.

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

- 리프레시 토큰은 자바스크립트에서 읽을 수 없도록 `HttpOnly` 쿠키로만 주고받는다.
- JWT 페이로드에는 최소 식별 정보인 `user_id`만 저장한다. (이메일, 이름, 권한 등은 저장하지 않는다)

### 1-3. 권한 (REQ-USER-005)

| 권한 | 값 | 접근 가능 범위 |
|---|---|---|
| 대기자 | `PENDING` | 마이페이지(`/api/v1/users/me` 관련 API)만 가능 |
| 스태프 | `STAFF` | 흉부 X-ray 관련 읽기·쓰기·수정 가능 |
| 어드민 | `ADMIN` | 모든 데이터 접근 가능 (회원 관리 포함) |

- 회원가입 직후 권한은 `PENDING`이다. 관리자가 권한을 변경해야 서비스를 이용할 수 있다.

### 1-4. 공통 값 형식

| 항목 | 형식 | 비고 |
|---|---|---|
| 이메일 | 이메일 형식, 최대 255자 | 중복 불가 |
| 비밀번호 | 8~20자, 영문·숫자·특수문자 각 1개 이상 | DB에는 argon2로 해싱해서 저장 |
| 이름 | 1~20자 | |
| 부서 | `MEDICAL`(의료), `DEV`(개발), `RESEARCH`(연구) | |
| 성별 | `M`, `F` | |
| 휴대폰 번호 | 숫자만 10~11자리 (예: `01012345678`) | 중복 불가 |

### 1-5. 공통 사용자 응답 객체 (`UserResponse`)

여러 API에서 사용자 정보를 돌려줄 때 같은 형식을 사용한다.

```json
{
  "id": 1,
  "email": "doctor@example.com",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "STAFF",
  "is_active": true
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 사용자 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서 (`MEDICAL`, `DEV`, `RESEARCH`) |
| gender | string | 성별 (`M`, `F`) |
| phone_number | string | 휴대폰 번호 |
| role | string | 권한 (`PENDING`, `STAFF`, `ADMIN`) |
| is_active | boolean | 계정 활성화 여부 |

- `hashed_password`는 어떤 응답에도 포함하지 않는다.

### 1-6. 공통 에러 응답

| 상태 코드 | 상황 | 예시 |
|---|---|---|
| 401 Unauthorized | 토큰이 없거나, 만료되었거나, 위조된 경우 | `{"detail": "인증 정보가 유효하지 않습니다."}` |
| 403 Forbidden | 권한이 부족한 경우 (예: STAFF가 관리자 API 호출) | `{"detail": "접근 권한이 없습니다."}` |
| 403 Forbidden | 비활성화된 계정인 경우 | `{"detail": "비활성화된 사용자입니다."}` |
| 404 Not Found | 대상 사용자가 없는 경우 | `{"detail": "사용자를 찾을 수 없습니다."}` |
| 409 Conflict | 이메일·휴대폰 번호가 이미 사용 중인 경우 | `{"detail": "이미 사용 중인 이메일입니다."}` |
| 422 Unprocessable Entity | 필수 값 누락, 형식 오류 | FastAPI 기본 검증 오류 형식 |

422 응답 형식:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### 1-7. 성능 (NFR-USER-003)

- 모든 User API는 3초 이내에 응답한다.

---

## 2. 회원가입 (담당: 장성은)

<!--
아래 형식으로 작성해 주세요. (로그인 API 예시 참고)
### 2-1. API 개요
### 2-2. 요청(Request)  - Headers / 본문 필드 / 쿼리 파라미터
### 2-3. 응답(Response) - 성공 / 실패
### 2-4. 비고
-->

---

## 3. 로그인 (담당: 엄태은)

### 3-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 로그인 API |
| 설명 | 회원가입한 사용자가 이메일과 비밀번호로 로그인하고, 액세스 토큰과 리프레시 토큰을 발급받는다. |
| 엔드포인트 | `/api/v1/auth/login` |
| 메서드 | `POST` |
| 인증 필요 여부 | N |
| 요구사항 | REQ-USER-002, NFR-USER-001 |

### 3-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| email | string | Y | 가입한 이메일 |
| password | string | Y | 비밀번호 |

```json
{
  "email": "doctor@example.com",
  "password": "Password1!"
}
```

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

### 3-3. 응답(Response)

**성공: 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "doctor@example.com",
    "name": "홍길동",
    "department": "MEDICAL",
    "gender": "M",
    "phone_number": "01012345678",
    "role": "STAFF",
    "is_active": true
  }
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| access_token | string | 30분 동안 유효한 JWT 액세스 토큰 |
| token_type | string | 토큰 인증 방식 (`bearer`) |
| expires_in | integer | 액세스 토큰 만료까지 남은 시간(초), 1800 |
| user | object | 로그인한 사용자 정보 (`UserResponse`, 1-5 참고) |

**응답 Headers**

| Key | 예시 값 | 설명 |
|---|---|---|
| Set-Cookie | `refresh_token=<JWT>; HttpOnly; SameSite=Lax; Max-Age=604800; Path=/api/v1/auth` | 7일 동안 유효한 리프레시 토큰 |

**실패**

- 401 Unauthorized: 이메일이 없거나 비밀번호가 틀린 경우

```json
{
  "detail": "이메일 또는 비밀번호가 일치하지 않습니다."
}
```

- 403 Forbidden: 비활성화된 계정인 경우

```json
{
  "detail": "비활성화된 사용자입니다."
}
```

- 422 Unprocessable Entity: 필수 값 누락, 이메일 형식 오류 (1-6 참고)

### 3-4. 비고

- 이메일이 없는 경우와 비밀번호가 틀린 경우 모두 **같은 메시지**를 돌려준다. 어느 쪽이 틀렸는지 알려 주면, 가입된 이메일인지 아닌지를 외부에서 알아낼 수 있기 때문이다.
- `PENDING` 권한도 로그인은 가능하다. (마이페이지는 이용할 수 있어야 하므로)
- 리프레시 토큰 쿠키의 `Path`를 `/api/v1/auth`로 제한해, 인증 관련 API를 호출할 때만 쿠키가 전송되도록 한다.
- 운영 환경(HTTPS)에서는 쿠키에 `Secure` 옵션을 추가한다.

---

## 4. 토큰 재발급 (담당: 엄태은)

### 4-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 액세스 토큰 재발급 API |
| 설명 | 액세스 토큰이 만료되었을 때, 쿠키의 리프레시 토큰으로 새 액세스 토큰을 발급받는다. |
| 엔드포인트 | `/api/v1/auth/token/refresh` |
| 메서드 | `POST` |
| 인증 필요 여부 | 리프레시 토큰 쿠키 필요 |
| 요구사항 | NFR-USER-001 |

### 4-2. 요청(Request)

**Headers / Cookie**

| Key | Value | 설명 |
|---|---|---|
| Cookie | `refresh_token=<JWT>` | 로그인 시 발급된 리프레시 토큰 (브라우저가 자동으로 전송) |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 요청 본문을 사용하지 않음 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

### 4-3. 응답(Response)

**성공: 200 OK**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| access_token | string | 새로 발급된 30분짜리 액세스 토큰 |
| token_type | string | `bearer` |
| expires_in | integer | 1800 |

**실패**

- 401 Unauthorized: 쿠키가 없거나, 리프레시 토큰이 만료·위조된 경우 → 다시 로그인해야 함

```json
{
  "detail": "다시 로그인해 주세요."
}
```

- 403 Forbidden: 비활성화된 계정인 경우

```json
{
  "detail": "비활성화된 사용자입니다."
}
```

### 4-4. 비고

- 리프레시 토큰까지 만료되면 401을 돌려주고, 클라이언트는 로그인 페이지로 이동한다.
- 토큰의 `type`이 `refresh`인지 확인한다. 액세스 토큰을 쿠키에 넣어 재발급을 시도하는 것을 막기 위해서다.
- 토큰의 `user_id`로 사용자를 다시 조회해, 탈퇴했거나 비활성화된 사용자에게는 발급하지 않는다.

---

## 5. 로그아웃 (담당: 엄태은)

### 5-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 로그아웃 API |
| 설명 | 리프레시 토큰 쿠키를 삭제해 로그아웃한다. |
| 엔드포인트 | `/api/v1/auth/logout` |
| 메서드 | `POST` |
| 인증 필요 여부 | N |
| 요구사항 | REQ-USER-003 |

### 5-2. 요청(Request)

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 요청 본문을 사용하지 않음 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

### 5-3. 응답(Response)

**성공: 204 No Content**

- 응답 본문 없음

**응답 Headers**

| Key | 예시 값 | 설명 |
|---|---|---|
| Set-Cookie | `refresh_token=""; Max-Age=0; Path=/api/v1/auth` | 리프레시 토큰 쿠키 삭제 |

### 5-4. 비고

- 인증을 요구하지 않는다. 액세스 토큰이 이미 만료된 상태에서도 로그아웃 버튼이 동작해야 하기 때문이다.
- 클라이언트는 메모리에 보관하던 액세스 토큰을 삭제하고 로그인 페이지로 이동한다.
- 서버는 토큰을 따로 저장하지 않으므로(Stateless), 이미 발급된 액세스 토큰은 만료(최대 30분)까지 유효하다.

---

## 6. 회원 목록 조회 (담당: 여현지)

<!--
REQ-USER-004 참고
- 쿼리 파라미터: 검색어(이메일 또는 이름), 부서 필터 등
- 응답: 회원 목록 (고유 ID, 이메일, 이름, 부서, 성별, 휴대폰 번호, 계정 활성화 여부)
- 권한: ADMIN만 가능 (아니면 403)
-->

---

## 7. 회원 권한 변경 (담당: 여현지)

<!--
REQ-USER-005 참고
- 경로 파라미터: user_id
- 본문: 변경할 권한 (PENDING / STAFF / ADMIN)
- 권한: ADMIN만 가능
-->

---

## 8. 마이페이지 조회 (담당: 김민준)

### API 기본 정보

| 항목 | 내용 |
|---|---|
| 요구사항 ID | REQ-USER-006 |
| HTTP Method | GET |
| URL | `/api/v1/users/me` |
| 기능 | 로그인한 사용자의 마이페이지 정보 조회 |
| 인증 | 필수 (Access Token) |
| 접근 권한 | PENDING, STAFF, ADMIN |

### 요청 (Request)

- Header: `Authorization: Bearer {access_token}`
- Path Parameter: 없음
- Query Parameter: 없음
- Request Body: 없음

### 성공 응답 (Response)

- HTTP Status: `200 OK`

```json
{
  "name": "홍길동",
  "email": "hong@example.com",
  "department": "DEV",
  "gender": "MALE",
  "phone_number": "010-1234-5678",
  "role": "PENDING"
}
```

※ 응답 값은 예시이며, 실제 필드명과 선택값은 팀 공통 모델 및 요구사항과 일치시킨다.

### 오류 응답

| HTTP Status | 발생 상황 |
|---|---|
| 401 Unauthorized | Access Token이 없거나 유효하지 않은 경우 |
| 404 Not Found | 인증된 사용자 계정이 DB에 존재하지 않는 경우 |

### 처리 흐름

1. Access Token으로 로그인 사용자를 확인한다.
2. 인증된 사용자의 정보를 DB에서 조회한다.
3. 이름, 이메일, 부서, 성별, 휴대폰 번호, 권한을 반환한다.
4. 비밀번호 및 비밀번호 해시는 응답에 포함하지 않는다.
5. PENDING 권한 사용자도 조회할 수 있다.
---

## 9. 회원 정보 수정 (담당: 김민준)

### API 기본 정보

| 항목 | 내용 |
|---|---|
| 요구사항 ID | REQ-USER-007 |
| HTTP Method | PATCH |
| URL | `/api/v1/users/me` |
| 기능 | 로그인한 사용자의 부서 및 휴대폰 번호 수정 |
| 인증 | 필수 (Access Token) |
| 접근 권한 | PENDING, STAFF, ADMIN |

### 요청 (Request)

- Header: `Authorization: Bearer {access_token}`
- Content-Type: `application/json`
- Path Parameter: 없음
- Query Parameter: 없음
- Request Body: 부서, 휴대폰 번호 (선택 항목)

**요청 예시**

```json
{
  "department": "DEV",
  "phone_number": "010-1234-5678"
}
```

**부분 수정 예시 — 휴대폰 번호만 변경**

```json
{
  "phone_number": "010-9876-5432"
}
```

- `department`: 변경할 부서 (선택)
- `phone_number`: 변경할 휴대폰 번호 (선택)
- 요청에 포함된 항목만 수정한다.
- 요청에 없는 항목은 기존 값을 유지한다.
- 이름, 이메일, 성별, 권한은 이 API로 수정할 수 없다.
- 부서의 허용값과 휴대폰 번호 형식은 팀 공통 모델 및 검증 기준을 따른다.
- 변경 항목이 없거나 허용되지 않은 항목이 전달되면 422 오류를 반환하도록 정의한다.

### 성공 응답 (Response)

- HTTP Status: `200 OK`

```json
{
  "name": "홍길동",
  "email": "hong@example.com",
  "department": "DEV",
  "gender": "MALE",
  "phone_number": "010-9876-5432",
  "role": "PENDING"
}
```

※ 응답은 수정 완료된 회원 정보이며, 비밀번호 및 비밀번호 해시는 포함하지 않는다.

### 오류 응답

| HTTP Status | 발생 상황 |
|---|---|
| 401 Unauthorized | Access Token이 없거나 유효하지 않은 경우 |
| 404 Not Found | 인증된 사용자 계정이 DB에 존재하지 않는 경우 |
| 409 Conflict | 변경하려는 휴대폰 번호를 다른 회원이 사용 중인 경우 |
| 422 Unprocessable Content | 부서·휴대폰 번호 형식이 잘못되었거나 유효하지 않은 요청인 경우 |

### 처리 흐름

1. Access Token으로 로그인 사용자를 확인한다.
2. DB에서 로그인한 사용자의 정보를 조회한다.
3. 요청 본문에 부서 또는 휴대폰 번호가 있는지 확인한다.
4. 전달된 값의 형식과 허용 범위를 검증한다.
5. 휴대폰 번호 변경 시 다른 회원과 중복되는지 확인한다.
6. 중복된 번호라면 409 오류를 반환한다.
7. 요청에 포함된 항목만 수정하고 나머지 정보는 유지한다.
8. 변경 사항을 DB에 저장한다.
9. 수정된 회원 정보를 반환한다.

---

## 10. 비밀번호 변경 (담당: 김민준)

### API 기본 정보

| 항목 | 내용 |
|---|---|
| 요구사항 ID | REQ-USER-008 |
| HTTP Method | PATCH |
| URL | `/api/v1/users/me/password` |
| 기능 | 로그인한 사용자의 비밀번호 변경 |
| 인증 | 필수 (Access Token) |
| 접근 권한 | PENDING, STAFF, ADMIN |

### 요청 (Request)

- Header: `Authorization: Bearer {access_token}`
- Content-Type: `application/json`
- Path Parameter: 없음
- Query Parameter: 없음
- Request Body: 기존 비밀번호, 새 비밀번호 (모두 필수)

**요청 예시**

```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**요청 필드 설명**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| current_password | string | Y | 현재 사용 중인 비밀번호 |
| new_password | string | Y | 새로 변경할 비밀번호 |

- 기존 비밀번호가 일치해야 변경할 수 있다.
- 새 비밀번호는 기존 비밀번호와 달라야 한다.
- 새 비밀번호는 팀 공통 비밀번호 정책을 충족해야 한다.
- 비밀번호는 평문으로 DB에 저장하지 않고 argon2 방식으로 해싱한다.

### 성공 응답 (Response)

- HTTP Status: `200 OK`

```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다."
}
```

- 변경된 비밀번호는 응답에 포함하지 않는다.
- 비밀번호 변경 후 기존 토큰 처리 방식은 팀 공통 인증 정책을 따른다.

### 오류 응답

| HTTP Status | 발생 상황 |
|---|---|
| 400 Bad Request | 기존 비밀번호가 일치하지 않거나 새 비밀번호가 기존 비밀번호와 같은 경우 |
| 401 Unauthorized | Access Token이 없거나 유효하지 않은 경우 |
| 404 Not Found | 인증된 사용자 계정이 DB에 존재하지 않는 경우 |
| 422 Unprocessable Content | 필수 항목 누락, 비밀번호 형식 또는 공통 정책 위반 |

### 처리 흐름

1. Access Token으로 로그인 사용자를 확인한다.
2. DB에서 로그인한 사용자의 계정을 조회한다.
3. 기존 비밀번호와 DB에 저장된 비밀번호 해시를 비교한다.
4. 기존 비밀번호가 틀리면 400 오류를 반환한다.
5. 새 비밀번호가 기존 비밀번호와 다른지 확인한다.
6. 새 비밀번호가 팀 공통 비밀번호 정책을 만족하는지 검증한다.
7. 새 비밀번호를 공통 argon2 해싱 함수로 암호화한다.
8. 기존 비밀번호 해시를 새 해시로 변경한다.
9. 변경 사항을 DB에 저장한다.
10. 성공 메시지를 반환한다.

### 보안 및 주의사항

- 비밀번호 원문을 DB나 로그에 기록하지 않는다.
- 로그인한 사용자 본인의 비밀번호만 변경할 수 있다.
- 기존 비밀번호 확인 및 해싱은 공통 인증 모듈을 사용한다.
- 비밀번호 변경 후 토큰 무효화 여부는 인증 담당자와 협의한다.

---

## 11. 회원 탈퇴 (담당: 장성은)

<!--
REQ-USER-009 참고
- 회원 정보를 DB에서 즉시 삭제 (Hard Delete)
- 성공 시 응답 코드, 리프레시 토큰 쿠키 처리 등
-->
