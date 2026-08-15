"""Embedder Google Gemini — endpoint embedContent (une requête par texte)."""

from __future__ import annotations

import httpx

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "text-embedding-004"


class GeminiEmbedder:
    name = "gemini"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._key = api_key
        self._model = model or DEFAULT_MODEL

    def available(self) -> bool:
        return bool(self._key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        url = f"{_BASE}/{self._model}:embedContent?key={self._key}"
        out: list[list[float]] = []
        async with httpx.AsyncClient(timeout=120) as client:
            for t in texts:
                body = {"content": {"parts": [{"text": t}]}}
                resp = await client.post(url, json=body, headers={"content-type": "application/json"})
                if resp.status_code != 200:
                    raise RuntimeError(f"gemini embed {resp.status_code}: {resp.text[:200]}")
                out.append(resp.json()["embedding"]["values"])
        return out
