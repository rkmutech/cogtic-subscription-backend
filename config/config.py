import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
   
class BaseConfig(BaseSettings):
    APP_NAME: str = "cogtic-subscription-backend"
    ENV_STAGE: Literal["development", "production", "test"] = "development"
    DB_URL: str = "postgresql://postgres:mysecret123@localhost/subscriptiondb"
    DB_FORCE_ROLLBACK: bool = False
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


class DevelopmentConfig(BaseConfig):
    ENV_STAGE: Literal["development"] = "development"
    DB_URL: str = "postgresql://postgres:mysecret123@localhost/subscriptiondb"
    DB_FORCE_ROLLBACK: bool = False

    model_config = SettingsConfigDict(
        env_prefix="DEV_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

def get_settings() -> BaseConfig:
    stage = os.getenv("ENV_STAGE", "development").lower()
    configs = {
        "development": DevelopmentConfig,
    }
    selected = configs.get(stage, DevelopmentConfig)
    return selected()


settings = get_settings()

  
