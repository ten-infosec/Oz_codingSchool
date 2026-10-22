# Git 브랜치 전략 정리

## 1. 브랜치 전략이란?

여러 명이 동시에 작업해도 서로의 코드에 영향을 주지 않도록, **브랜치를 어떤 종류로 나누고, 어디서 분기해서 어디로 병합할지** 팀이 미리 정한 약속이다.
기능·이슈 단위로 작업을 추적할 수 있고, 버전 단위로 관리해 배포 안정성을 높여 준다.

대표적인 전략으로 **Git Flow**와 **GitHub Flow**가 있다.

---

## 2. Git Flow

2010년 Vincent Driessen이 제안한 모델로, 역할별로 브랜치를 나눠 **개발 중인 코드와 출시된 코드를 엄격하게 분리**하는 것이 핵심이다.

### 2-1. 브랜치 구성

| 브랜치 | 역할 | 분기 위치 | 병합 위치 |
|---|---|---|---|
| `main` | 실제 출시(운영) 중인 코드 | - | - |
| `develop` | 다음 출시를 위해 개발한 기능을 통합 | main | release |
| `feature/*` | 기능 하나를 개발 | develop | develop |
| `release/*` | 출시 전 최종 테스트·버그 수정 | develop | main, develop |
| `hotfix/*` | 출시된 제품의 긴급 버그 수정 | main | main, develop |

- `main`, `develop`은 계속 유지되고, 나머지는 작업이 끝나면 삭제한다.
- release·hotfix를 main에 병합한 뒤 **develop에도 반드시 병합**한다. 그래야 이후 개발이 수정된 안정 버전 위에서 이어진다.

### 2-2. 작업 흐름

```
feature/* ──PR──▶ develop ──▶ release/* ──▶ main (출시)
                                  │              │
                                  └─▶ develop ◀──┘
                                       ▲
                        hotfix/* ──────┴──▶ main
```

1. develop을 최신화한 뒤 `feature/기능명` 브랜치를 만든다.
2. 기능 개발 → commit → push → **PR(base: develop)** → 리뷰·승인 → merge → 브랜치 삭제
3. 출시 시점에 develop에서 release를 만들어 테스트하고, 버그는 release에서 수정한다.
4. release를 main에 병합해 출시하고, develop에도 병합한다.
5. 출시 후 급한 버그는 main에서 hotfix를 만들어 고친 뒤 main과 develop에 병합한다.

### 2-3. 실무 사례에서 본 특징
- develop을 **알파(내부) 테스트 환경**, release를 **베타(출시 직전) 테스트 환경**으로 쓰기도 한다.
- 큰 기능은 부모 feature(`feature/10`) 아래 자식 feature(`feature/10-1`)를 두고, 자식 → 부모 PR에서 코드 리뷰를 한다.
- main에 배포한 뒤 develop·release를 바로 최신화하지 않으면 공용 브랜치가 꼬여 복구가 어려워진다.

### 2-4. 장단점
- **장점**: 출시 코드와 개발 코드가 분리되어 안정적이고, 버전 단위 관리에 강하다.
- **단점**: 브랜치 종류가 많아 규칙이 복잡하고, 작은 팀·짧은 프로젝트에는 관리 부담이 크다.

---

## 3. GitHub Flow

GitHub가 제안한 **단순하고 빠른** 모델이다. 핵심 브랜치는 `main` 하나뿐이다.

### 3-1. 브랜치 구성

| 브랜치 | 역할 |
|---|---|
| `main` | 항상 배포 가능한 상태의 코드 |
| `feature/*` (작업 브랜치) | 기능 추가·수정용. main에서 분기 → PR → main에 병합 |

### 3-2. 작업 흐름

1. main을 최신화하고 작업 브랜치를 만든다.
2. 작업 → commit → push
3. PR(base: main) 생성, 리뷰어 지정
4. 리뷰 → 피드백 반영(같은 브랜치에 push하면 PR에 자동 반영) → 승인
5. main에 merge → 작업 브랜치 삭제 → (지속적 배포 환경이면 곧바로 배포)

### 3-3. 함께 쓰는 GitHub 기능
- **브랜치 보호 규칙(Rulesets)**: main 병합 전 PR·승인 필수 (무료 계정은 Public 레포에서 사용 가능)
- **GitHub Actions**: PR마다 테스트 자동 실행, 실패하면 병합 차단
- **Issues**: 할 일 등록 후 커밋 메시지에 `close #번호` → 기본 브랜치에 병합되면 이슈 자동 종료
- **Labels / Milestones**: 작업 종류 표시, 마감일 관리

### 3-4. 장단점
- **장점**: 규칙이 단순해 배우기 쉽고, 기능 단위로 빠르게 반영할 수 있다.
- **단점**: main에 바로 병합되므로 리뷰·테스트가 부실하면 main이 깨질 수 있고, 여러 버전을 동시에 관리하기 어렵다.

---

## 4. 비교 요약

| 구분 | Git Flow | GitHub Flow |
|---|---|---|
| 핵심 브랜치 | main + develop | main |
| 보조 브랜치 | feature, release, hotfix | feature(작업 브랜치) |
| feature 분기 위치 | develop | main |
| 출시 관리 | release 브랜치로 명시적 관리 | 병합 = 배포 |
| 복잡도 | 높음 | 낮음 |
| 적합한 상황 | 정기 출시, 대규모 팀, 버전 관리 필요 | 수시 배포, 소규모 팀, 짧은 프로젝트 |

---

## 5. PR 병합 방식

| GitHub 옵션 | 결과 | 특징 |
|---|---|---|
| Create a merge commit | 병합 커밋 생성 | 병합 기록이 명확하게 남음 |
| Squash and merge | 여러 커밋을 하나로 압축 | 히스토리가 깔끔하지만 개별 기록이 사라짐 |
| Rebase and merge | 커밋을 일직선으로 쌓음 | 병합 커밋이 없지만 충돌 시 복잡할 수 있음 |

---

## 6. 우리 팀의 선택

**main / develop / feature 3개 브랜치를 쓰는 간소화 Git Flow**를 사용한다. (강사님 권장 방식)

### 선택 이유
- 기간이 2주, 팀원이 4명이라 release·hotfix까지 운영하는 Git Flow 전체는 과하다.
- 그렇다고 GitHub Flow처럼 main에 바로 병합하면, 실행되는 코드가 main을 깨뜨릴 위험이 있다.
- 그래서 **develop을 중간 통합 브랜치로 두고**, 검증된 상태에서만 main에 병합한다.

### 브랜치 규칙

| 브랜치 | 규칙 |
|---|---|
| `main` | 최종본. 직접 push 금지, 마감 시점에 develop에서만 병합 (단, md 문서 과제는 main 직접 push 허용) |
| `develop` | 개발 통합 브랜치. 모든 기능은 PR로만 병합 |
| `feature/기능명` | 각자 작업용. develop에서 분기, 병합 후 삭제 (예: `feature/practice-create`) |

### 작업 순서

```bash
git switch develop
git pull
git switch -c feature/기능명
# 코드 작성
git add 파일
git commit -m "feat: 기능 설명"
git push -u origin feature/기능명
```

이후 GitHub에서 PR(base: **develop**) → 팀원 1명 이상 리뷰·승인 → **Create a merge commit**으로 병합 → 브랜치 삭제

### 지킬 것
- 작업 시작 전 항상 develop 최신화
- 같은 파일을 여럿이 고칠 때는 구역을 나눠서 작업 (충돌 방지)
- force push는 개인 feature 브랜치에서만, develop·main에는 금지
- 리뷰 코멘트도 존댓말·쿠션어로
