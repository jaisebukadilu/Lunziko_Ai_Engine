"""Adaptateur Claude (Anthropic) — appel REST direct via httpx (pas de SDK lourd).

Endpoint /v1/messages, header anthropic-version 2023-06-01. Modèle par défaut :
claude-opus-4-8 (le plus capable ; configurable par requête). Pas de temperature
(retirée sur Opus 4.8/4.7).
"""

from __future__ import annotations

import httpx

from ai_engine.modules.provider.base import (
    ChatMessage, ChatResult, ProviderError, ToolCall, ToolChatResult, ToolSpec,
)

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-opus-4-8"


def build_claude_tool_body(messages: list[dict], tools: list[ToolSpec],
                           system: str | None, model: str, max_tokens: int) -> dict:
    """Convertit messages neutres + outils vers le format Messages API d'Anthropic."""
    conv: list[dict] = []
    for m in messages:
        role = m["role"]
        if role == "tool":
            conv.append({"role": "user", "content": [{
                "type": "tool_result", "tool_use_id": m["tool_call_id"],
                "content": m.get("content", "")}]})
        elif role == "assistant" and m.get("tool_calls"):
            blocks: list[dict] = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m["tool_calls"]:
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"],
                               "input": tc.get("arguments", {})})
            conv.append({"role": "assistant", "content": blocks})
        else:
            conv.append({"role": role, "content": m.get("content", "")})
    body: dict = {"model": model, "max_tokens": max_tokens, "messages": conv}
    if system:
        body["system"] = system
    if tools:
        body["tools"] = [{"name": t.name, "description": t.description,
                          "input_schema": t.parameters} for t in tools]
    return body


def parse_claude_tool_response(data: dict, fallback_model: str) -> ToolChatResult:
    text, calls = "", []
    for b in data.get("content", []):
        if b.get("type") == "text":
            text += b.get("text", "")
        elif b.get("type") == "tool_use":
            calls.append(ToolCall(id=b["id"], name=b["name"], arguments=b.get("input", {})))
    return ToolChatResult(
        content=text, tool_calls=calls, provider="claude",
        model=data.get("model", fallback_model),
        stop_reason="tool_use" if calls else "end")


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

    def supports_tools(self) -> bool:
        return True

    async def chat_with_tools(
        self, messages: list[dict], tools: list[ToolSpec], *,
        system: str | None = None, model: str | None = None, max_tokens: int = 4096,
    ) -> ToolChatResult:
        body = build_claude_tool_body(messages, tools, system, model or DEFAULT_MODEL, max_tokens)
        headers = {"x-api-key": self._key, "anthropic-version": _VERSION,
                   "content-type": "application/json"}
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(_URL, json=body, headers=headers)
        if resp.status_code != 200:
            raise ProviderError(f"claude {resp.status_code}: {resp.text[:300]}")
        return parse_claude_tool_response(resp.json(), body["model"])
