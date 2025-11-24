"""
Helper de stockage objet (S3/MinIO) pour les pieces jointes.

Infos utiles:
- Instancie deux clients: un pour l'upload et un pour signer les URLs publiques.
- Force l'utilisation de signatures v4 et peut forcer le path-style pour MinIO/compat.
- Les erreurs reseau boto sont converties en RuntimeError pour remonter clairement a l'API.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from ..config import settings


class ObjectStorage:
    """Fin wrapper boto3 pour upload et generation de liens presignes."""

    def __init__(
        self,
        bucket: str,
        *,
        endpoint_url: str | None,
        access_key: str,
        secret_key: str,
        region: str | None,
        use_ssl: bool,
        force_path_style: bool,
        public_endpoint_url: str | None = None,
    ) -> None:
        # --- Configuration des clients S3 (upload et signature) ---
        session = boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path" if force_path_style else "auto"},
        )
        self.client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=config,
            use_ssl=use_ssl,
        )
        signing_endpoint = public_endpoint_url or endpoint_url
        signing_use_ssl = use_ssl if public_endpoint_url is None else public_endpoint_url.lower().startswith("https://")
        self.signing_client = session.client(
            "s3",
            endpoint_url=signing_endpoint,
            config=config,
            use_ssl=signing_use_ssl,
        )
        self.bucket = bucket

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        *,
        content_type: str | None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Charge un flux binaire dans le bucket cible avec metadonnees optionnelles."""
        extra_args: dict[str, str] = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata
        try:
            self.client.upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra_args or None)
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Unable to upload attachment") from exc

    def generate_presigned_url(self, key: str, *, expires_in: int) -> str:
        """Genere une URL presignee pour telecharger un objet pendant une duree limitee."""
        try:
            return self.signing_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("Unable to generate download URL") from exc

    def object_url(self, key: str) -> str:
        """Retourne une URL interne de type s3://bucket/key."""
        return f"s3://{self.bucket}/{key}"

    def key_from_url(self, storage_url: str) -> str:
        """Extrait la cle d'objet a partir d'une URL s3://bucket/key."""
        prefix = f"s3://{self.bucket}/"
        if storage_url.startswith(prefix):
            return storage_url[len(prefix) :]
        return storage_url

    def generate_key(self, conversation_id: str, *, filename: str | None = None) -> str:
        """Cree une cle unique pour une conversation, en conservant l'extension du fichier."""
        safe_name = Path(filename or "attachment").name.replace(" ", "_")
        suffix = Path(safe_name).suffix.lower()
        return f"conversations/{conversation_id}/{uuid.uuid4()}{suffix}"


@lru_cache()
def get_storage() -> ObjectStorage | None:
    """Instancie le stockage objet si toutes les variables requises sont presentes."""
    if not settings.STORAGE_BUCKET:
        return None
    required = [settings.STORAGE_ACCESS_KEY, settings.STORAGE_SECRET_KEY]
    if not all(required):
        return None
    return ObjectStorage(
        settings.STORAGE_BUCKET,
        endpoint_url=settings.STORAGE_ENDPOINT,
        access_key=settings.STORAGE_ACCESS_KEY,  # type: ignore[arg-type]
        secret_key=settings.STORAGE_SECRET_KEY,  # type: ignore[arg-type]
        region=settings.STORAGE_REGION,
        use_ssl=settings.STORAGE_USE_SSL,
        force_path_style=settings.STORAGE_FORCE_PATH_STYLE,
        public_endpoint_url=settings.STORAGE_PUBLIC_ENDPOINT,
    )


__all__ = ["ObjectStorage", "get_storage"]
