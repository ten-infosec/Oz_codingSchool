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

### 2-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원가입 API |
| 설명 | 사내 의료인, 개발 실무진, 연구진이 회원가입을 한다. 가입 직후 권한은 `PENDING`(대기자)이다. |
| 엔드포인트 | `/api/v1/users/signup` |
| 메서드 | `POST` |
| 인증 필요 여부 | N |
| 요구사항 | REQ-USER-001 |

### 2-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Content-Type | application/json | 요청 본문 형식 |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| email | string | Y | 이메일 (이메일 형식, 최대 255자, 중복 불가) |
| password | string | Y | 비밀번호 (8~20자, 영문·숫자·특수문자 각 1개 이상) |
| name | string | Y | 이름 (1~20자) |
| department | string | Y | 부서 (`MEDICAL`, `DEV`, `RESEARCH`) |
| gender | string | Y | 성별 (`M`, `F`) |
| phone_number | string | Y | 휴대폰 번호 (숫자만 10~11자리, 중복 불가) |

```json
{
  "email": "doctor@example.com",
  "password": "Password1!",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678"
}
```

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

### 2-3. 응답(Response)

**성공: 201 Created**

```json
{
  "id": 1,
  "email": "doctor@example.com",
  "name": "홍길동",
  "department": "MEDICAL",
  "gender": "M",
  "phone_number": "01012345678",
  "role": "PENDING",
  "is_active": true
}
```

| 필드명 | 타입 | 설명 |
|---|---|---|
| id | integer | 사용자 고유 ID |
| email | string | 이메일 |
| name | string | 이름 |
| department | string | 부서 |
| gender | string | 성별 |
| phone_number | string | 휴대폰 번호 |
| role | string | 권한 (가입 직후 `PENDING`) |
| is_active | boolean | 계정 활성화 여부 (가입 직후 `true`) |

- 응답 형식은 `UserResponse`(1-5 참고)와 같다.

**실패**

- 409 Conflict: 이미 가입된 이메일인 경우

```json
{
  "detail": "이미 사용 중인 이메일입니다."
}
```

- 409 Conflict: 이미 가입된 휴대폰 번호인 경우

```json
{
  "detail": "이미 사용 중인 휴대폰 번호입니다."
}
```

- 422 Unprocessable Entity: 필수 값 누락, 이메일·비밀번호·휴대폰 번호 형식 오류 (1-6 참고)

### 2-4. 비고

- 비밀번호는 argon2로 해싱해서 `hashed_password`에 저장하고, 응답에는 포함하지 않는다.
- 권한(`role`)은 요청으로 받지 않고 서버에서 `PENDING`으로 저장한다. 사용자가 스스로 `ADMIN`으로 가입하는 것을 막기 위해서다.
- 회원가입 후 자동 로그인은 하지 않는다. 토큰은 로그인 API(3번)에서 발급받는다.

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

<!--
REQ-USER-006 참고
- 응답: 이름, 이메일, 부서, 성별, 휴대폰 번호, 권한
- PENDING 권한도 접근 가능
-->

---

## 9. 회원 정보 수정 (담당: 김민준)

<!--
REQ-USER-007 참고
- 부분 수정(Partial): 부서, 휴대폰 번호 중 보낸 항목만 수정
- 휴대폰 번호 중복 시 409
-->

---

## 10. 비밀번호 변경 (담당: 김민준)

<!--
REQ-USER-008 참고
- 본문: 기존 비밀번호, 새 비밀번호
- 기존 비밀번호가 틀리면 에러 (상태 코드는 명세에서 정해 주세요)
-->

---

## 11. 회원 탈퇴 (담당: 장성은)

### 11-1. API 개요

| 항목 | 내용 |
|---|---|
| API 이름 | 회원 탈퇴 API |
| 설명 | 로그인한 사용자가 마이페이지에서 회원 탈퇴를 한다. 회원 정보는 DB에서 즉시 삭제된다. |
| 엔드포인트 | `/api/v1/users/me` |
| 메서드 | `DELETE` |
| 인증 필요 여부 | Y |
| 요구사항 | REQ-USER-009 |

### 11-2. 요청(Request)

**Headers**

| Key | Value | 설명 |
|---|---|---|
| Authorization | `Bearer <access_token>` | 로그인 시 발급받은 액세스 토큰 |

**본문 필드**

| 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 요청 본문을 사용하지 않음 |

**쿼리 파라미터**

| 쿼리 파라미터명 | 타입 | 필수 | 설명 |
|---|---|---|---|
| 없음 | - | - | 쿼리 파라미터를 사용하지 않음 |

### 11-3. 응답(Response)

**성공: 204 No Content**

- 응답 본문 없음

**응답 Headers**

| Key | 예시 값 | 설명 |
|---|---|---|
| Set-Cookie | `refresh_token=""; Max-Age=0; Path=/api/v1/auth` | 리프레시 토큰 쿠키 삭제 |

**실패**

- 401 Unauthorized: 토큰이 없거나, 만료되었거나, 위조된 경우

```json
{
  "detail": "인증 정보가 유효하지 않습니다."
}
```

- 403 Forbidden: 비활성화된 계정인 경우

```json
{
  "detail": "비활성화된 사용자입니다."
}
```

### 11-4. 비고

- 회원 정보는 DB에서 바로 삭제한다. (Hard Delete)
- 모든 권한(`PENDING` 포함)이 탈퇴할 수 있다.
- 탈퇴 후에는 리프레시 토큰 쿠키도 삭제한다. 쿠키를 지울 때는 로그아웃(5번)과 같은 `Path`(`/api/v1/auth`)를 줘야 지워진다.
- 탈퇴 전에 발급된 액세스 토큰으로 요청하면, 토큰 주인이 DB에 없으므로 401을 돌려준다.
