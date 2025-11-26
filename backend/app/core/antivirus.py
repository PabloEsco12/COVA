"""
############################################################
# Module : Antivirus (ClamAV)
# Auteur : Valentin Masurelle
# Date   : 2025-05-04
#
# Description:
# - Integre ClamAV via clamd si la config est presente.
# - Rejette les fichiers infectes, remonte 502 en cas d'indispo scanner.
#
# Points de vigilance:
# - Le scanner est desactive si clamd ou host sont absents.
# - Toujours fermer/supprimer le fichier temporaire cote service appelant.
############################################################
"""

from __future__ import annotations

from functools import lru_cache
import logging

from fastapi import HTTPException, status

from ..config import settings

try:
    import clamd
except ImportError:  # pragma: no cover - optional dependency
    clamd = None  # type: ignore


class AntivirusScanner:
    """Wrapper autour de ClamAV. Desactive si la configuration est absente."""

    def __init__(self, host: str | None, port: int) -> None:
        self.host = host
        self.port = port
        self.enabled = bool(host and clamd)
        self._client = None
        self.logger = logging.getLogger(__name__)

    # --- Section: Connexion et client ---
    def _ensure_client(self):
        if not self.enabled:
            return None
        if self._client is None:
            self._client = clamd.ClamdNetworkSocket(host=self.host, port=self.port)  # type: ignore[attr-defined]
        return self._client

    # --- Section: Scan des fichiers ---
    def scan_path(self, path: str) -> None:
        client = self._ensure_client()
        if not client:
            return
        try:
            result = client.scan(path)
        except Exception as exc:  # pragma: no cover - network errors
            # Si le scanner est indisponible, on journalise et on degrade gracieusement
            self.logger.warning("Antivirus indisponible, scan ignore pour %s : %s", path, exc)
            self.enabled = False
            return
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
