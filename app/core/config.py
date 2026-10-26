from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ===== Database =====
    DB_USER: str = "root"
    DB_PASSWORD: str = "password1234"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"

    # ===== JWT =====
    # 토큰 서명에 쓰는 비밀키 (기본값 없음 → .env에 반드시 있어야 서버가 켜진다)
    SECRET_KEY: str
    # 서명 알고리즘
    JWT_ALGORITHM: str = "HS256"
    # 액세스 토큰 만료 시간(분) - NFR-USER-001: 30분
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 리프레시 토큰 만료 시간(일) - NFR-USER-001: 7일
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
