"""Chiffrement de la mémoire — AES-256-GCM si clé + `cryptography` dispo, sinon dev en clair.

`AE_MEMORY_KEY` = base64 de 32 octets. Sans clé (ou sans la lib), on retombe sur un mode
« dev en clair » explicitement marqué (jamais silencieux) pour que l'AI Engine reste lançable.
"""

from __future__ import annotations

import base64
import os
from functools import lru_cache

from ai_engine.config import get_settings

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    _HAS_CRYPTO = True
except Exception:  # pragma: no cover
    _HAS_CRYPTO = False


class PlaintextCipher:
    """Repli dev : préfixe explicite, aucun chiffrement (à ne pas utiliser en prod)."""

    mode = "plaintext-dev"

    def encrypt(self, text: str) -> str:
        return "plain:" + text

    def decrypt(self, blob: str) -> str:
        return blob[6:] if blob.startswith("plain:") else blob


class AesGcmCipher:
    mode = "aes-256-gcm"

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AE_MEMORY_KEY doit faire 32 octets (base64).")
        self._aes = AESGCM(key)

    def encrypt(self, text: str) -> str:
        nonce = os.urandom(12)
        ct = self._aes.encrypt(nonce, text.encode("utf-8"), None)
        return "gcm:" + base64.b64encode(nonce + ct).decode("ascii")

    def decrypt(self, blob: str) -> str:
        raw = base64.b64decode(blob[4:] if blob.startswith("gcm:") else blob)
        nonce, ct = raw[:12], raw[12:]
        return self._aes.decrypt(nonce, ct, None).decode("utf-8")


@lru_cache
def get_cipher():
    key_b64 = get_settings().ae_memory_key
    if key_b64 and _HAS_CRYPTO:
        return AesGcmCipher(base64.b64decode(key_b64))
    return PlaintextCipher()
