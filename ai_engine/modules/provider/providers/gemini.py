"""Adaptateur Google Gemini — API generateContent via httpx."""

from __future__ import annotations

import httpx

from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    name = "gemini"

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
        mdl = model or DEFAULT_MODEL
        contents = [
            {"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]}
            for m in messages
        ]
        payload: dict = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": max_tokens},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        url = f"{_BASE}/{mdl}:generateContent?key={self._key}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload, headers={"content-type": "application/json"})
        if resp.status_code != 200:
            raise ProviderError(f"gemini {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        cand = (data.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {})
        return ChatResult(
            content=text,
            provider=self.name,
            model=mdl,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
        )
