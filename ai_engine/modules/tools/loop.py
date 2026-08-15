"""Boucle de tool-calling : modèle → (demande d'outil → exécution → re-boucle) → réponse.

Provider-agnostique : `chat` et `execute` sont injectables (testable sans réseau).
Messages neutres : {role:user|assistant|tool, content, tool_calls?, tool_call_id?, name?}.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from ai_engine.modules.provider.base import ToolChatResult, ToolSpec

ChatFn = Callable[[list[dict], list[ToolSpec], str | None], Awaitable[ToolChatResult]]
ExecFn = Callable[[str, dict], Awaitable[str]]


async def run_tool_loop(
    query: str,
    *,
    specs: list[ToolSpec],
    chat: ChatFn,
    execute: ExecFn,
    system: str | None = None,
    max_iters: int = 5,
) -> dict:
    messages: list[dict] = [{"role": "user", "content": query}]
    trace: list[dict] = []
    for step in range(1, max_iters + 1):
        res = await chat(messages, specs, system)
        if not res.tool_calls:
            return {"answer": res.content, "iterations": step, "tool_trace": trace,
                    "provider": res.provider, "model": res.model}
        messages.append({"role": "assistant", "content": res.content,
                         "tool_calls": [tc.model_dump() for tc in res.tool_calls]})
        for tc in res.tool_calls:
            result = await execute(tc.name, tc.arguments)
            trace.append({"tool": tc.name, "arguments": tc.arguments, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name,
                             "content": result})
    # budget d'itérations épuisé : dernière tentative sans outils
    final = await chat(messages, [], system)
    return {"answer": final.content, "iterations": max_iters, "tool_trace": trace,
            "provider": final.provider, "model": final.model, "truncated": True}
