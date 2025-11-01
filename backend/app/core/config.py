"""Application configuration module."""

from functools import lru_cache
from typing import List

from pydantic import EmailStr, Field
from pydantic.functional_validators import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.dev", ".env.prod"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, alias="API_DEBUG")

    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    REDIS_URL: str = Field(..., env="REDIS_URL")

    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 30, env="REFRESH_TOKEN_EXPIRE_MINUTES")

    EMAIL_CONFIRMATION_EXPIRY_HOURS: int = Field(default=24, env="EMAIL_CONFIRMATION_EXPIRY_HOURS")
    PASSWORD_RESET_EXPIRY_MINUTES: int = Field(default=60, env="PASSWORD_RESET_EXPIRY_MINUTES")

    FRONTEND_URL: str = Field(default="http://localhost:5175", env="FRONTEND_URL")

    SMTP_HOST: str | None = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=465, env="SMTP_PORT")
    SMTP_USERNAME: str | None = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: str | None = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=False, env="SMTP_USE_TLS")
    SMTP_FROM_EMAIL: EmailStr | None = Field(default=None, env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str | None = Field(default=None, env="SMTP_FROM_NAME")

    TOTP_ISSUER: str = Field(default="COVA Secure Messaging", env="TOTP_ISSUER")

    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=list)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            if not value:
                return []
            return [origin.strip().rstrip("/") for origin in value.split(",")]
        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value]
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
