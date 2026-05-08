from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Chat"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sixmin@localhost:5432/aichat"

    # JWT
    JWT_SECRET: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_DAYS: int = 7

    # OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Doubao / Volcengine
    VOICE_APP_ID: str = ""
    VOICE_ACCESS_KEY: str = ""
    VOICE_RESOURCE_ID: str = "volc.speech.dialog"
    VOICE_APP_KEY: str = "PlgvMymc7f3tQnJ6"
    VOICE_WS_URL: str = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
