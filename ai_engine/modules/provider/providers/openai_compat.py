"""Adaptateur OpenAI-compatible — sert OpenAI, DeepSeek, Mistral et un serveur local
(llama.cpp / vLLM) : même API `/chat/completions`, seul le base_url + la clé changent.
"""

from __future__ import annotations

import httpx

from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError


class OpenAICompatProvider:
    def __init__(self, name: str, base_url: str, api_key: str, default_model: str) -> None:
        self.name = name
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._default_model = default_model

    def available(self) -> bool:
        # Un serveur local peut ne pas exiger de clé ; suffit d'avoir une base URL.
        return bool(self._key) or bool(self._base)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
    ) -> ChatResult:
        msgs: list[dict] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += [{"role": m.role, "content": m.content} for m in messages]
        payload = {"model": model or self._default_model, "messages": msgs, "max_tokens": max_tokens}
        headers = {"content-type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base}/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            raise ProviderError(f"{self.name} {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        choice = (data.get("choices") or [{}])[0]
        text = (choice.get("message") or {}).get("content", "") or ""
        usage = data.get("usage", {})
        return ChatResult(
            content=text,
            provider=self.name,
            model=data.get("model", payload["model"]),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
