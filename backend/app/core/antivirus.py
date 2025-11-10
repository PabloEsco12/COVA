"""Lightweight antivirus client (ClamAV) integration."""

from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, status

from ..config import settings

try:
    import clamd
except ImportError:  # pragma: no cover - optional dependency
    clamd = None  # type: ignore


class AntivirusScanner:
    """Wrapper around ClamAV. Disabled if configuration missing."""

    def __init__(self, host: str | None, port: int) -> None:
        self.host = host
        self.port = port
        self.enabled = bool(host and clamd)
        self._client = None

    def _ensure_client(self):
        if not self.enabled:
            return None
        if self._client is None:
            self._client = clamd.ClamdNetworkSocket(host=self.host, port=self.port)  # type: ignore[attr-defined]
        return self._client

    def scan_path(self, path: str) -> None:
        client = self._ensure_client()
        if not client:
            return
        try:
            result = client.scan(path)
        except Exception as exc:  # pragma: no cover - network errors
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Antivirus indisponible") from exc
        if not result:
            return
        _, (status_label, signature) = next(iter(result.items()))
        if status_label == "FOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fichier malveillant détecté ({signature})",
            )


@lru_cache()
def get_antivirus_scanner() -> AntivirusScanner:
    return AntivirusScanner(settings.ANTIVIRUS_HOST, settings.ANTIVIRUS_PORT)


__all__ = ["AntivirusScanner", "get_antivirus_scanner"]
