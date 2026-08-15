"""Authentification du gateway par clé d'API — PROPRE à l'AI Engine (pas Supabase Auth).

Si aucune clé n'est configurée (AE_API_KEYS vide), l'accès est libre (dev/standalone).
"""

from __future__ import annotations

from fastapi import Header, HTTPException

from ai_engine.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    keys = get_settings().api_keys
    if not keys:
        return  # mode ouvert (dev / usage local)
    if x_api_key not in keys:
        raise HTTPException(status_code=401, detail="Clé d'API invalide ou absente (X-API-Key)")


async def require_bearer_or_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> None:
    """Auth des endpoints compatibles OpenAI : accepte `Authorization: Bearer <clé>` OU `X-API-Key`.

    Vide (AE_API_KEYS non configuré) => accès libre (dev). Permet aux clients OpenAI
    (Open WebUI, LocalAI, Continue…) de s'authentifier de façon standard.
    """
    keys = get_settings().api_keys
    if not keys:
        return
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token in keys or x_api_key in keys:
        return
    raise HTTPException(status_code=401, detail="Clé invalide (Authorization: Bearer ou X-API-Key)")
