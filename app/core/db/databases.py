from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from urllib.parse import quote_plus

from app.core.config import settings


DATABASE_PREFIX = "mysql+asyncmy://"
# 비밀번호에 @ : / # 같은 특수문자가 있으면 주소가 잘못 끊기므로 URL 인코딩한다 (예: @ → %40)
DATABASE_URI = f"{quote_plus(settings.DB_USER)}:{quote_plus(settings.DB_PASSWORD)}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
DATABASE_URL = f"{DATABASE_PREFIX}{DATABASE_URI}"

# 비동기 엔진 생성
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
# 비동기 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
# 모델 베이스 생성
Base = declarative_base()

# 세션 생성 함수
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db
