import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

# practice_apis.py에서 만든 router를 가져온다
from app.apis.practice_apis import router as practice_router
# 4일차 User API 라우터
from app.apis.auth import router as auth_router
from app.apis.users import router as users_router
from app.apis.users import admin_router
# 5일차 환자·진료기록 API 라우터
from app.apis.patients import router as patients_router
from app.apis.medical_records import router as medical_records_router
# 6일차 AI 폐렴 예측 API 라우터
from app.apis.analyses import router as analyses_router
from worker.model import get_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 켜질 때 AI 모델을 한 번 메모리에 올려 둔다 (첫 예측 요청도 3초 이내로)
    get_model()
    yield


app = FastAPI(lifespan=lifespan)

# practice 라우터 등록 (맨 아래 catch_all보다 반드시 위에 있어야 함)
app.include_router(practice_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(patients_router)
app.include_router(medical_records_router)
app.include_router(analyses_router)

BASE_DIR = Path(__file__).resolve().parent.parent

# 만약 static, media 폴더가 존재하지 않으면 생성
if not (BASE_DIR / "static").exists():
    os.mkdir(BASE_DIR / "static")
if not (BASE_DIR / "media").exists():
    os.mkdir(BASE_DIR / "media")

# 'static' 폴더를 '/static' 경로로 마운트 (CSS, JS 파일 서빙용)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# 'media' 폴더를 '/media' 경로로 마운트 (사용자 업로드 파일 서빙용)
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


@app.get(path="/healthcheck", status_code=200, include_in_schema=False)
async def healthcheck():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    # API나 정적 파일 경로는 제외 (FastAPI가 먼저 매칭하지 못한 경우에만 실행됨)
    if (
        path.startswith("api/v1")
        or path.startswith("static/")
        or path.startswith("media/")
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=404)
    return FileResponse(BASE_DIR / "static" / "index.html")
