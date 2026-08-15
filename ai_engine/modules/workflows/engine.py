"""WorkflowEngine — exécute des pipelines nommés, persiste chaque run (StoragePort).

Chaque étape est une coroutine `ctx -> maj(ctx)`. Exécution séquentielle synchrone,
arrêt à la première erreur, run journalisé (statut, étapes, durée) dans `workflow_runs`.
Les workflows prédéfinis composent provider / rag / memory / knowledge.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Awaitable, Callable

from ai_engine.core.registry import get_storage
from ai_engine.modules.knowledge.engine import get_knowledge_engine
from ai_engine.modules.memory.engine import get_memory_engine
from ai_engine.modules.provider.base import ChatMessage
from ai_engine.modules.provider.manager import get_provider_manager
from ai_engine.modules.rag.service import get_rag_service

Step = Callable[[dict], Awaitable[dict]]
_RUNS_NS = "workflow_runs"


# --- Étapes réutilisables -------------------------------------------------
async def _step_summarize(ctx: dict) -> dict:
    res = await get_provider_manager().chat(
        [ChatMessage(role="user", content=ctx["text"])],
        provider=ctx.get("provider"),
        system="Résume le texte suivant de façon concise et fidèle. Réponds dans sa langue.",
        max_tokens=ctx.get("max_tokens", 1024),
    )
    return {"result": res.content, "provider_used": res.provider}


async def _step_doc_analysis(ctx: dict) -> dict:
    res = await get_provider_manager().chat(
        [ChatMessage(role="user", content=ctx["text"])],
        provider=ctx.get("provider"),
        system="Analyse le document : 1) résumé 2) points clés 3) sentiment global. Format Markdown.",
        max_tokens=ctx.get("max_tokens", 1500),
    )
    return {"result": res.content, "provider_used": res.provider}


async def _step_rag_answer(ctx: dict) -> dict:
    out = await get_rag_service().query(
        ctx["namespace"], ctx["query"], k=ctx.get("k", 5), provider=ctx.get("provider")
    )
    return {"result": out["answer"].content, "sources": out["sources"]}


async def _step_gather_context(ctx: dict) -> dict:
    parts: list[str] = []
    if ctx.get("user_id"):
        mem = await get_memory_engine().recall(ctx["user_id"], ctx["query"], 3)
        parts += [f"[mémoire] {m['key']}: {m['value']}" for m in mem]
    if ctx.get("org"):
        kn = await get_knowledge_engine().search(ctx["org"], ctx["query"], 3)
        parts += [f"[connaissance] {k['title']}: {k.get('content','')}" for k in kn]
    return {"context": "\n".join(parts)}


async def _step_contextual_answer(ctx: dict) -> dict:
    res = await get_provider_manager().chat(
        [ChatMessage(role="user", content=ctx["query"])],
        provider=ctx.get("provider"),
        system="Réponds en t'appuyant sur le CONTEXTE.\n\nCONTEXTE:\n" + ctx.get("context", ""),
        max_tokens=ctx.get("max_tokens", 1024),
    )
    return {"result": res.content, "provider_used": res.provider}


BUILTIN: dict[str, list[tuple[str, Step]]] = {
    "summarize": [("summarize", _step_summarize)],
    "documentAnalysis": [("analyze", _step_doc_analysis)],
    "ragAnswer": [("rag", _step_rag_answer)],
    "contextualChat": [("gather", _step_gather_context), ("answer", _step_contextual_answer)],
}


class WorkflowEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._registry = BUILTIN

    def types(self) -> list[str]:
        return list(self._registry.keys())

    async def run(self, wf_type: str, inputs: dict) -> dict:
        steps = self._registry.get(wf_type)
        if steps is None:
            raise KeyError(f"workflow inconnu: {wf_type}")
        run_id = uuid.uuid4().hex
        ctx: dict = dict(inputs)
        log: list[dict] = []
        status = "succeeded"
        t0 = time.perf_counter()
        for name, fn in steps:
            s0 = time.perf_counter()
            try:
                ctx.update(await fn(ctx) or {})
                log.append({"step": name, "ok": True, "ms": round((time.perf_counter() - s0) * 1000)})
            except Exception as e:
                log.append({"step": name, "ok": False, "error": str(e)[:300]})
                status = "failed"
                break
        rec = {
            "id": run_id,
            "type": wf_type,
            "status": status,
            "steps": log,
            "duration_ms": round((time.perf_counter() - t0) * 1000),
            "result": ctx.get("result"),
            "sources": ctx.get("sources"),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._store.put(_RUNS_NS, run_id, rec)
        return rec

    def get_run(self, run_id: str) -> dict | None:
        return self._store.get(_RUNS_NS, run_id)

    def list_runs(self) -> list[dict]:
        return self._store.list(_RUNS_NS)


def get_workflow_engine() -> WorkflowEngine:
    return WorkflowEngine()
