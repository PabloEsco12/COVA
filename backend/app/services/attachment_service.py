"""
Service de gestion des pieces jointes: upload, scan antivirus et jetons d'acces temporaires.

Infos utiles:
- Stockage externalise via ObjectStorage, avec generation de liens presignes.
- Scan antivirus optionnel (injection de AntivirusScanner).
- Limite de taille via settings.ATTACHMENT_MAX_BYTES et jetons JWT signes pour securiser les metadonnees.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, UploadFile, status
from jose import jwt

from ..config import settings
from ..core.storage import ObjectStorage
from ..core.antivirus import AntivirusScanner
from app.models import UserAccount


CHUNK_SIZE = 1024 * 1024


@dataclass
class AttachmentDescriptor:
    """Payload issu du jeton d'upload, necessaire pour persister la piece jointe."""

    storage_key: str
    storage_url: str
    file_name: str | None
    mime_type: str | None
    size_bytes: int
    sha256: str
    encryption_metadata: dict[str, Any] | None = None


class AttachmentService:
    """Gere le flux d'upload, les controles antivirus et l'emission de jetons d'upload."""

    def __init__(self, storage: ObjectStorage, scanner: AntivirusScanner | None = None) -> None:
        """Initialise le service avec le stockage objet et, si present, un scanner antivirus."""
        self.storage = storage
        self.scanner = scanner

    async def upload_attachment(
        self,
        *,
        conversation_id: uuid.UUID,
        user: UserAccount,
        file: UploadFile,
        encryption_metadata: dict | None = None,
    ) -> dict:
        """Stream le fichier vers le stockage, applique limites/scan, et renvoie le jeton d'upload."""
        if not file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nom de fichier manquant.")

        tmp = tempfile.NamedTemporaryFile(delete=False)
        sha256 = hashlib.sha256()
        total = 0
        try:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.ATTACHMENT_MAX_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Fichier trop volumineux.")
                tmp.write(chunk)
                sha256.update(chunk)
        finally:
            await file.close()
            tmp.close()

        if settings.ATTACHMENT_ALLOWED_MIME and file.content_type:
            if file.content_type not in settings.ATTACHMENT_ALLOWED_MIME:
                os.unlink(tmp.name)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type de fichier non autorisé.")

        if self.scanner:
            self.scanner.scan_path(tmp.name)

        key = self.storage.generate_key(str(conversation_id), filename=file.filename)
        with open(tmp.name, "rb") as payload:
            self.storage.upload_fileobj(
                payload,
                key,
                content_type=file.content_type,
                metadata={"conversation": str(conversation_id)},
            )
        os.unlink(tmp.name)

        storage_url = self.storage.object_url(key)
        sha_hex = sha256.hexdigest()
        token = self._encode_token(
            conversation_id=conversation_id,
            user_id=user.id,
            storage_key=key,
            storage_url=storage_url,
            file_name=file.filename,
            mime_type=file.content_type,
            size_bytes=total,
            sha256_hex=sha_hex,
            encryption_metadata=encryption_metadata,
        )
        download_url = self.storage.generate_presigned_url(
            key,
            expires_in=settings.ATTACHMENT_DOWNLOAD_TTL_SECONDS,
        )
        return {
            "upload_token": token,
            "file_name": file.filename,
            "mime_type": file.content_type,
            "size_bytes": total,
            "sha256": sha_hex,
            "download_url": download_url,
            "encryption": encryption_metadata or {},
        }

    def decode_token(
        self,
        upload_token: str,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AttachmentDescriptor:
        """Decode et valide un jeton d'upload pour recuperer les metadonnees du fichier."""
        try:
            payload = jwt.decode(
                upload_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except Exception as exc:  # pragma: no cover - library handled elsewhere
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pièce jointe invalide.") from exc

        if payload.get("kind") != "attachment_upload":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Jeton de pièce jointe invalide.")
        if payload.get("conv") != str(conversation_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pièce jointe hors conversation.")
        if payload.get("sub") != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Jeton non autorisé.")

        return AttachmentDescriptor(
            storage_key=payload["key"],
            storage_url=payload["storage_url"],
            file_name=payload.get("name"),
            mime_type=payload.get("mime"),
            size_bytes=int(payload.get("bytes", 0)),
            sha256=payload.get("sha256"),
            encryption_metadata=payload.get("enc"),
        )

    def _encode_token(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        storage_key: str,
        storage_url: str,
        file_name: str,
        mime_type: str | None,
        size_bytes: int,
        sha256_hex: str,
        encryption_metadata: dict | None,
    ) -> str:
        """Cree un JWT court terme encapsulant les metadonnees de l'upload."""
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.ATTACHMENT_UPLOAD_TOKEN_TTL_MINUTES)
        payload = {
            "kind": "attachment_upload",
            "sub": str(user_id),
            "conv": str(conversation_id),
            "key": storage_key,
            "storage_url": storage_url,
            "name": file_name,
            "mime": mime_type,
            "bytes": size_bytes,
            "sha256": sha256_hex,
            "enc": encryption_metadata,
            "exp": expires,
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


__all__ = ["AttachmentService", "AttachmentDescriptor"]
