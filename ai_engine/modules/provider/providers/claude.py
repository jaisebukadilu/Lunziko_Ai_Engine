"""Adaptateur Claude (Anthropic) — appel REST direct via httpx (pas de SDK lourd).

Endpoint /v1/messages, header anthropic-version 2023-06-01. Modèle par défaut :
claude-opus-4-8 (le plus capable ; configurable par requête). Pas de temperature
(retirée sur Opus 4.8/4.7).
"""

from __future__ import annotations

import httpx

from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"


class ClaudeProvider:
    name = "claude"

    def __init__(self, api_key: str) -> None:
        self._key = api_key

    def available(self) -> bool:
        return bool(self._key)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> ChatResult:
        payload: dict = {
            "model": model or DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self._key,
            "anthropic-version": _VERSION,
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            raise ProviderError(f"claude {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage", {})
        return ChatResult(
            content=text,
            provider=self.name,
            model=data.get("model", payload["model"]),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
