"""AI Orchestrator — le chef d'orchestre de LAIA.

Flux : intent → contexte → décomposition (Task Intelligence) → sélection de Brains → plan.
`plan()` s'arrête au plan (100% offline). `run()` exécute en plus les sous-tâches servables par
un Brain actif via le Provider Manager (best-effort) et valide la sortie. Réutilise les modules
existants (neural router, context assembler, brain registry, provider) — sans les modifier.
"""

from __future__ import annotations

from ai_engine.modules.orchestrator.blackboard import get_blackboard
from ai_engine.modules.orchestrator.brains import get_brain_registry
from ai_engine.modules.orchestrator.task_intelligence import decompose
from ai_engine.modules.orchestrator.validation import validate

_BRAIN_ARTIFACT_TYPE = {"code": "code", "ui_ux": "ui", "data": "data"}


class AIOrchestrator:
    async def _intent(self, goal: str) -> dict:
        try:
            from ai_engine.modules.neural.router_engine import get_neural_router
            r = await get_neural_router().route(goal)
            return {"capability": r["capability"], "confidence": r["confidence"]}
        except Exception:
            return {"capability": "general", "confidence": 0.0}

    async def _context(self, user_id: str | None, app: str | None, goal: str) -> dict | None:
        if not user_id:
            return None
        try:
            from ai_engine.modules.context.assembler import get_context_assembler
            ctx = await get_context_assembler().assemble(user_id, query=goal, app=app)
            return {"system_block": ctx.get("system_block", ""), "temporal": ctx.get("temporal")}
        except Exception:
            return None

    async def plan(self, goal: str, *, user_id: str | None = None, app: str | None = None) -> dict:
        intent = await self._intent(goal)
        context = await self._context(user_id, app, goal)
        subtasks = decompose(goal)
        reg = get_brain_registry()
        brains_used = sorted({s["brain"] for s in subtasks})
        engines_used = sorted({e for s in subtasks for e in s["engines"]})
        bb = get_blackboard()
        task = bb.create(goal, user_id=user_id, app=app)
        bb.update(task["id"], plan=subtasks, context=context or {},
                  decisions=[{"intent": intent, "brains": brains_used}])
        return {
            "task_id": task["id"], "goal": goal, "intent": intent,
            "brains": [{"id": b, "status": (reg.get(b) or {}).get("status", "active")} for b in brains_used],
            "engines": engines_used, "plan": subtasks,
            "context": {"available": context is not None},
        }

    async def run(self, goal: str, *, user_id: str | None = None, app: str | None = None,
                  provider: str | None = None, max_tokens: int = 800) -> dict:
        planned = await self.plan(goal, user_id=user_id, app=app)
        bb = get_blackboard()
        reg = get_brain_registry()
        tid = planned["task_id"]
        system_block = ""
        rec = bb.get(tid)
        if rec:
            system_block = (rec.get("context") or {}).get("system_block", "")

        results = []
        for st in planned["plan"]:
            brain = reg.get(st["brain"]) or {}
            if brain.get("status") != "active":
                results.append({"subtask": st["id"], "brain": st["brain"],
                                "status": "deferred", "reason": "Brain non actif (modèle à venir)"})
                bb.append(tid, "outputs", results[-1])
                continue
            system = (f"Tu es le {brain.get('name', st['brain'])}. "
                      f"Traite : {st['description']}.")
            if system_block:
                system += "\n\n" + system_block
            try:
                from ai_engine.modules.provider.base import ChatMessage
                from ai_engine.modules.provider.manager import get_provider_manager
                ans = await get_provider_manager().chat(
                    [ChatMessage(role="user", content=st["description"])],
                    provider=provider, system=system, max_tokens=max_tokens)
                content = ans.content
                vtype = _BRAIN_ARTIFACT_TYPE.get(st["brain"], "text")
                v = validate(vtype, content)
                out = {"subtask": st["id"], "brain": st["brain"], "status": "done",
                       "content": content, "validation": v}
                bb.append(tid, "artifacts", {"subtask": st["id"], "type": vtype})
                bb.append(tid, "validation", v)
            except Exception as e:
                out = {"subtask": st["id"], "brain": st["brain"], "status": "error", "error": str(e)}
                bb.append(tid, "errors", {"subtask": st["id"], "error": str(e)})
            results.append(out)
            bb.append(tid, "outputs", {"subtask": st["id"], "status": out["status"]})

        done = sum(1 for r in results if r["status"] == "done")
        bb.update(tid, status="completed" if done else "partial")
        return {"task_id": tid, "goal": goal, "results": results,
                "summary": {"subtasks": len(results), "done": done,
                            "deferred": sum(1 for r in results if r["status"] == "deferred"),
                            "errors": sum(1 for r in results if r["status"] == "error")}}


def get_orchestrator() -> AIOrchestrator:
    return AIOrchestrator()
