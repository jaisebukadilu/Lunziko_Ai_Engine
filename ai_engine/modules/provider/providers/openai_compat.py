"""Adaptateur OpenAI-compatible — sert OpenAI, DeepSeek, Mistral et un serveur local
(llama.cpp / vLLM) : même API `/chat/completions`, seul le base_url + la clé changent.
"""

from __future__ import annotations

import json

import httpx

from ai_engine.modules.provider.base import (
    ChatMessage, ChatResult, ProviderError, ToolCall, ToolChatResult, ToolSpec,
)


def build_openai_tool_messages(messages: list[dict], system: str | None) -> list[dict]:
    """Convertit messages neutres vers le format OpenAI (avec tool_calls / role tool)."""
    out: list[dict] = []
    if system:
        out.append({"role": "system", "content": system})
    for m in messages:
        role = m["role"]
        if role == "tool":
            out.append({"role": "tool", "tool_call_id": m["tool_call_id"],
                        "content": m.get("content", "")})
        elif role == "assistant" and m.get("tool_calls"):
            out.append({"role": "assistant", "content": m.get("content") or None,
                        "tool_calls": [{"id": tc["id"], "type": "function",
                                        "function": {"name": tc["name"],
                                                     "arguments": json.dumps(tc.get("arguments", {}))}}
                                       for tc in m["tool_calls"]]})
        else:
            out.append({"role": role, "content": m.get("content", "")})
    return out


def parse_openai_tool_response(data: dict, name: str, fallback_model: str) -> ToolChatResult:
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    calls = []
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        args = fn.get("arguments") or "{}"
        try:
            args = json.loads(args) if isinstance(args, str) else args
        except json.JSONDecodeError:
            args = {}
        calls.append(ToolCall(id=tc.get("id", fn.get("name", "")), name=fn.get("name", ""), arguments=args))
    return ToolChatResult(
        content=msg.get("content") or "", tool_calls=calls, provider=name,
        model=data.get("model", fallback_model),
        stop_reason="tool_use" if calls else "end")


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

    def supports_tools(self) -> bool:
        return True

    async def chat_with_tools(
        self, messages: list[dict], tools: list[ToolSpec], *,
        system: str | None = None, model: str | None = None, max_tokens: int = 4096,
    ) -> ToolChatResult:
        payload: dict = {
            "model": model or self._default_model,
            "messages": build_openai_tool_messages(messages, system),
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = [{"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.parameters}}
                for t in tools]
        headers = {"content-type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base}/chat/completions", json=payload, headers=headers)
        if resp.status_code != 200:
            raise ProviderError(f"{self.name} {resp.status_code}: {resp.text[:300]}")
        return parse_openai_tool_response(resp.json(), self.name, payload["model"])
