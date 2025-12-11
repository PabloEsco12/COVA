from __future__ import annotations

import base64
import os
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.models import Message
from ...config import settings
from .conversation_base import ConversationBase


class ConversationCryptoMixin(ConversationBase):
    """Chiffrement/déchiffrement des contenus de message."""

    def _extract_plaintext(self, message: Message) -> str:
        """Extrait du texte lisible depuis le champ ciphertext (utilisé pour prévisualisation)."""
        if message.encryption_scheme == "rsa-oaep-aesgcm":
            try:
                return self._decrypt_ciphertext(message)
            except Exception:
                pass
        return self._decode_plaintext(message.ciphertext)

    def _decode_plaintext(self, ciphertext: object) -> str:
        """Decode un message en clair UTF-8 ou renvoie une représentation texte."""
        if isinstance(ciphertext, (bytes, bytearray, memoryview)):
            return bytes(ciphertext).decode("utf-8", errors="ignore")
        return str(ciphertext or "")

    def _encrypt_content(self, *, conversation_id, content: str) -> Tuple[bytes, str, dict]:
        """Chiffre le contenu si la clé est configurée, sinon retourne du plaintext encodé."""
        if not self._encryption_enabled:
            return content.encode("utf-8"), "plaintext", {"encoding": "utf-8"}

        aes_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        aad = str(conversation_id).encode("utf-8")

        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, content.encode("utf-8"), aad)

        encrypted_key = self._rsa_public_key.encrypt(
            aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )

        metadata = {
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "enc_key": base64.b64encode(encrypted_key).decode("ascii"),
            "aad": base64.b64encode(aad).decode("ascii"),
            "encoding": "utf-8",
            "algo": "aes-256-gcm",
        }
        return ciphertext, "rsa-oaep-aesgcm", metadata

    def _decrypt_ciphertext(self, message: Message) -> str:
        """Déchiffre un message avec schéma rsa-oaep-aesgcm."""
        metadata = message.encryption_metadata or {}
        enc_key_b64 = metadata.get("enc_key")
        nonce_b64 = metadata.get("nonce")
        aad_b64 = metadata.get("aad")
        if not enc_key_b64 or not nonce_b64 or not self._rsa_private_key:
            return self._decode_plaintext(message.ciphertext)

        encrypted_key = base64.b64decode(enc_key_b64)
        nonce = base64.b64decode(nonce_b64)
        aad = base64.b64decode(aad_b64) if aad_b64 else None

        aes_key = self._rsa_private_key.decrypt(
            encrypted_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, bytes(message.ciphertext), aad)
        encoding = metadata.get("encoding") or "utf-8"
        return plaintext.decode(encoding, errors="ignore")

    def _load_rsa_public_key(self):
        pem = settings.MESSAGE_RSA_PUBLIC_KEY
        if not pem:
            return None
        try:
            return serialization.load_pem_public_key(pem.encode("utf-8"))
        except Exception:
            return None

    def _load_rsa_private_key(self):
        pem = settings.MESSAGE_RSA_PRIVATE_KEY
        if not pem:
            return None
        try:
            return serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
        except Exception:
            return None
