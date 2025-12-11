"""
############################################################
# Module : config (Settings Pydantic)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Paramétrage central de l'application via BaseSettings.
# - Chargé depuis .env(.local/.dev/.prod/.docker), non sensible à la casse.
# - Typage fort pour DB, JWT, SMTP, Storage, AV, CORS, etc.
############################################################
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration typée chargée depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.dev", ".env.prod", ".env.docker"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "Cova Messaging API v2"
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = Field(..., description="SQLAlchemy connection string")

    # JWT / Security
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_PRIVATE_KEY: str | None = None  # Utilisé si algorithme asymétrique (ex: RS256)
    JWT_PUBLIC_KEY: str | None = None   # Utilisé si algorithme asymétrique (ex: RS256)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 30)
    MESSAGE_ENCRYPTION_ENABLED: bool = False
    MESSAGE_RSA_PUBLIC_KEY: str | None = None
    MESSAGE_RSA_PRIVATE_KEY: str | None = None

    # SMTP / Notifications (Email)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 465
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "COVA Notifications"
    SMTP_USE_TLS: bool = False
    SMTP_USE_SSL: bool = False

    PUBLIC_BASE_URL: str = "http://localhost:8000"
    FRONTEND_ORIGIN: str = "http://localhost:5176"

    # Organisation / Admin
    DEFAULT_ORG_NAME: str = "COVA Messages"
    DEFAULT_ORG_SLUG: str = "cova-messages"
    DEFAULT_ADMIN_EMAIL: str = "covamessages3@gmail.com"

    MEDIA_ROOT: str = "static"
    AVATAR_MAX_BYTES: int = 2_000_000
    AVATAR_MAX_SIZE: int = 512

    # Stockage d'objets (pièces jointes)
    STORAGE_ENDPOINT: str | None = None
    STORAGE_PUBLIC_ENDPOINT: str | None = None
    STORAGE_ACCESS_KEY: str | None = None
    STORAGE_SECRET_KEY: str | None = None
    STORAGE_REGION: str | None = None
    STORAGE_BUCKET: str | None = None
    STORAGE_USE_SSL: bool = True
    STORAGE_FORCE_PATH_STYLE: bool = False

    ATTACHMENT_MAX_BYTES: int = 25_000_000
    ATTACHMENT_ALLOWED_MIME: List[str] = Field(
        default_factory=lambda: [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/gif",
            "text/plain",
            "application/zip",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]
    )
    ATTACHMENT_DOWNLOAD_TTL_SECONDS: int = 300
    ATTACHMENT_UPLOAD_TOKEN_TTL_MINUTES: int = 60

    ANTIVIRUS_HOST: str | None = None
    ANTIVIRUS_PORT: int = 3310

    # CORS / Frontend
    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=list)

    # Redis (pour temps réel ultérieur)
    REDIS_URL: str | None = None


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


settings = get_settings()
