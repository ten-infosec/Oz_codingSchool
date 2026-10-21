# Team Rules

## 1. 팀 운영 규칙

### 1-1. 코어 타임
- 매일 15:10~16:00 팀별 과제 시간에 모이기
- 카메라 필수 ON, 회의 중 마이크 적극 사용

### 1-2. 호칭과 말투
- 서로 "oo님"으로 부르고 존댓말·쿠션어 사용하기
- 의견이 다를 땐 감정보다 근거로 이야기하기

### 1-3. 적극적인 참여
- 눈치 보지 않고 의견 내기
- 막히는 부분은 30분 이상 혼자 붙잡지 말고 팀에 공유하기
- 일정이 생겨 참여가 어려우면 미리 알리기

### 1-4. 과제 제출
- Stage별 Notion 링크 + 역할·기여도는 각자 LMS에 제출
- 마감 전날까지 팀 작업을 마무리하는 것을 목표로 하기

## 2. 역할 분담

| 이름 | GitHub | 주 담당 |
|---|---|---|
| 엄태은 (팀장) | ten-infosec | AI 판독 API(모델 서빙), Git 관리 |
| 장성은 | jsejj87 | |
| 김민준 | klas98765-pixel | |
| 여현지 | yeohj1226 | |

- 역할은 "주 담당"이며, 모든 Stage 과제는 함께 공부하고 진행한다
- 모든 팀원은 Stage마다 최소 1개 이상 커밋·PR을 남긴다

### 역할별 상세 설명

#### ① AI 판독 API (모델 서빙) + Git 관리
- 하는 일: 의사가 X-ray 이미지를 올리면, 폐렴 판독 모델이 "정상/폐렴"과 확률을 돌려주는 API 만들기
  - `POST /predict` : 이미지 업로드 → 전처리 → 모델 예측 → 결과(JSON) 반환
  - 서버가 켜질 때 모델을 1번만 불러오기 (lifespan)
  - 판독 결과를 DB에 저장 (환자와 연결)
- 주로 다루는 곳: `app/apis/`(판독 라우터), `app/services/`(예측 로직)
- Git 관리: develop 브랜치 생성, PR 최종 merge, develop → main 병합
- 연결: DB 모델(③)의 판독 기록 테이블, 환자 API(②)의 환자 정보와 연결됨

#### ② 환자 관리 API (CRUD)
- 하는 일: 백오피스에서 환자를 등록·조회·수정·삭제하는 API 만들기
  - `POST /patients` 등록 / `GET /patients` 목록 / `GET /patients/{id}` 상세
  - `PATCH /patients/{id}` 수정 / `DELETE /patients/{id}` 삭제
  - 없는 환자를 찾으면 404 에러 등 상태 코드 처리
- 주로 다루는 곳: `app/schemas/`(요청·응답 데이터 형식), `app/repositories/`(DB 읽기·쓰기), `app/services/`, `app/apis/`
- 연결: DB 모델(③)이 먼저 있어야 저장 가능, 판독 API(①)와 통계(④)가 환자 데이터를 사용

#### ③ DB 모델·마이그레이션
- 하는 일: 데이터를 저장할 "표(테이블)" 설계와 생성
  - ERD를 보고 `app/models/`에 테이블 모델 작성 (환자, 판독 기록 등)
  - Alembic으로 마이그레이션(테이블 생성·변경 기록) 수행
  - 어떤 DB를 쓸지(SQLite, MySQL 등) 팀 논의 주도, `.env` DB 연결 설정 정리
  - DB Viewer로 테이블 확인 후 캡처 → `docs/3일차_db_migration.md`
- 주로 다루는 곳: `app/models/`, `app/core/db/`, `alembic/`
- 연결: 다른 모든 기능의 기초라 가장 먼저 필요함 (Stage 3)

#### ④ 통계 API · 대시보드 · 문서 정리
- 하는 일: 쌓인 데이터를 한눈에 보여주는 기능 + 팀 문서 관리
  - 통계 API: 전체 환자 수, 폐렴 판정 비율, 날짜별 판독 건수 등 집계
  - 대시보드: 통계를 차트·표로 보여주는 화면
  - 문서: Stage별 `docs/*.md` 작성 취합, Notion 정리
- 주로 다루는 곳: `app/apis/`(통계 라우터), `app/templates/`, `app/static/`, `docs/`
- 연결: 환자(②)·판독(①) 데이터가 쌓여야 의미 있는 통계가 나옴

### 작업 순서 (의존 관계)
DB 모델(③) → 환자 API(②) → 판독 API(①) → 통계·대시보드(④) → Docker 배포(전원)
- 앞 단계가 늦어지면 뒤 단계가 막히므로, 서로 진행 상황을 자주 공유한다

## 3. Git & GitHub 규칙

### 3-1. 브랜치 전략
- main: 최종본. 직접 push 금지, 마지막에 develop에서만 병합
- develop: 개발 통합 브랜치. 모든 기능은 PR로 여기에 병합
- feature/기능명: 각자 작업용 브랜치 (develop에서 분기)
  - 예) feature/patient-api, feature/predict-api
- 단, md 문서만 올리는 과제는 main에 바로 올려도 된다 (강사님 안내)

### 3-2. 작업 순서
1. 작업 시작 전 항상 git pull로 최신 상태 받기
2. develop에서 feature 브랜치 생성
3. 작업 → add → commit → push
4. Pull Request 생성 (base: develop)
5. 팀원 1명 이상 리뷰·승인 후 merge
6. merge 후 feature 브랜치 삭제

### 3-3. 커밋 메시지
- feat: 기능 추가 / fix: 버그 수정 / docs: 문서 / refactor: 코드 정리 / chore: 설정·기타
- 예) feat: 환자 등록 API 추가, docs: 1일차 팀 규칙 작성

### 3-4. PR 리뷰
- 리뷰 코멘트도 존댓말·쿠션어로 작성하기
- 리뷰 요청을 받으면 가능한 한 당일 안에 확인하기

### 3-5. 올리지 않을 파일
- .env (DB 비밀번호·API 키 등 비밀 정보)
- 모델 가중치 파일(.pth 등) 같은 대용량 파일
