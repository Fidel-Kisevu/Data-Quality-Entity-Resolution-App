from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "DataQ"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./dataguard.db"

    # Auth (simple MVP)
    SECRET_KEY: str = "change-me-in-production-dataq-mvp"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Source priority (locked)
    SOURCE_PRIORITY: list[str] = ["ERP", "CRM", "MKT"]

    # Matching thresholds
    MATCH_PROBABLE_THRESHOLD: float = 0.90
    MATCH_POSSIBLE_THRESHOLD: float = 0.75

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
