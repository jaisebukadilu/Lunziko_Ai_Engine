"""Embedder OpenAI-compatible — OpenAI, Mistral, serveur local (Ollama /v1, vLLM).

Endpoint `/embeddings` : body {model, input:[...]}, réponse data[].embedding.
"""

from __future__ import annotations

import httpx


class OpenAICompatEmbedder:
    def __init__(self, name: str, base_url: str, api_key: str, model: str) -> None:
        self.name = name
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._model = model

    def available(self) -> bool:
        return bool(self._key) or bool(self._base)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        headers = {"content-type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        payload = {"model": self._model, "input": texts}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base}/embeddings", json=payload, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"{self.name} embed {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return [d["embedding"] for d in data.get("data", [])]
