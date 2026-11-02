# ===== Base Image =====
# 로컬과 같은 파이썬 3.13, 불필요한 패키지를 뺀 slim 버전으로 이미지 크기를 줄인다
FROM python:3.13-slim


# ===== Package Manager (uv) =====
# 공식 uv 이미지에서 실행 파일만 복사해 온다 → pip로 설치하는 것보다 빠르고 가볍다
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

# 가상환경을 /app 밖(/opt/venv)에 만든다
# → docker-compose에서 프로젝트 폴더를 /app에 마운트해도 컨테이너의 가상환경이 가려지지 않는다
# UV_CONCURRENT_INSTALLS=1: 패키지를 한 번에 하나씩 설치해 메모리 사용을 줄인다
#   (PyTorch 압축을 여러 개 동시에 풀면 노트북 Docker Desktop의 빌드 엔진이 메모리 부족으로 멈출 수 있다)
# UV_NO_CACHE=1: 내려받은 파일을 캐시에 따로 남기지 않아 디스크·이미지 용량을 줄인다
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_CONCURRENT_INSTALLS=1 \
    UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# 이후 명령은 모두 /app 폴더 기준으로 실행한다
WORKDIR /app

# → uv와 실행 환경을 준비하겠다


# ===== Dependencies =====
# 의존성 목록만 먼저 복사해서 설치한다
# 소스 코드만 바뀌면 이 단계는 캐시를 그대로 써서 다시 빌드할 때 빨라진다
COPY pyproject.toml uv.lock ./

# --frozen: uv.lock에 적힌 버전 그대로 설치 (팀원 모두 같은 버전)
# --no-dev: 개발용 패키지 제외
# --no-install-project: 아직 소스가 없으므로 라이브러리만 설치
RUN uv sync --frozen --no-dev --no-install-project

# → 잠금 파일 기준으로 라이브러리만 먼저 설치하겠다


# ===== Source Code =====
# .dockerignore(app/Dockerfile.dockerignore)에 적힌 파일은 빼고 프로젝트 전체를 복사한다
COPY . .

# 컨테이너가 8000번 포트를 쓴다는 표시 (실제 연결은 docker run -p / compose ports)
EXPOSE 8000

# 운영용 실행 명령: fastapi run = uvicorn으로 app/main.py 실행 (--reload 없음)
# 개발할 때는 docker-compose.yml의 command가 이 명령을 덮어써서 --reload로 실행한다
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

# → 소스를 복사하고 FastAPI 서버를 8000번 포트로 실행하겠다
