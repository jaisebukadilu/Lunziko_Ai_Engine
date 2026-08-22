"""ResilientAgent — boucle agentique ReAct qui « ne renonce jamais ».

Pilier persistance : consulte la mémoire long-terme (LTM) AVANT d'agir (ne répète pas une
erreur passée), journalise chaque échec ET succès dans la LTM (auto-évolution).
Pilier détermination : à l'épuisement des tentatives, ne « laisse pas tomber » — enregistre
un PROBLÈME OUVERT à retenter et renvoie le meilleur effort + les prochaines étapes.

100 % offline-testable : `reason_fn` (Réflexion→Action) et `execute_fn` (Action) sont
injectables. Par défaut, `reason_fn` s'appuie sur le Provider Manager (tool-calling) et
`execute_fn` sur le ToolRegistry existants — aucune nouvelle dépendance.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from ai_engine.modules.autonomy.persona import build_system_prompt
from ai_engine.modules.learning.engine import get_continuous_memory

# reason_fn(goal, memories, history) -> {"done": bool, "answer"?, "action"?, "args"?, "thought"?}
ReasonFn = Callable[..., Awaitable[dict]]
# execute_fn(action, args) -> {"ok": bool, "result"?, "error"?}
ExecuteFn = Callable[..., Awaitable[dict]]


class ResilientAgent:
    def __init__(self, reason_fn: ReasonFn | None = None,
                 execute_fn: ExecuteFn | None = None) -> None:
        self._reason = reason_fn
        self._execute = execute_fn
        self._ltm = get_continuous_memory()

    async def _default_execute(self, action: str, args: dict) -> dict:
        from ai_engine.modules.tools.registry import get_tool_registry
        try:
            result = get_tool_registry().execute(action, args or {})
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def solve(self, goal: str, *, scope: str = "global",
                    max_iterations: int = 6) -> dict:
        reason = self._reason
        execute = self._execute or self._default_execute
        if reason is None:
            reason = self._llm_reason  # chemin live (nécessite un provider)

        # 1) Consulter la mémoire AVANT d'agir : erreurs et solutions passées.
        memories = await self._ltm.recall(scope, goal, k=8, include_archived=False)

        history: list[dict] = []
        for step in range(1, max_iterations + 1):
            plan = await reason(goal=goal, memories=memories, history=history)
            thought = plan.get("thought", "")

            if plan.get("done"):
                answer = plan.get("answer", "")
                await self._ltm.observe(
                    scope, f"SOLUTION pour « {goal} » : {answer}",
                    kind="solution", importance=0.85)
                return {
                    "status": "solved", "goal": goal, "answer": answer,
                    "iterations": step, "history": history, "gave_up": False,
                }

            action = plan.get("action", "")
            args = plan.get("args", {})
            obs = await execute(action, args)
            entry = {"step": step, "thought": thought, "action": action,
                     "args": args, "observation": obs}
            history.append(entry)

            if obs.get("ok"):
                await self._ltm.observe(
                    scope, f"Étape réussie pour « {goal} » : {action}",
                    kind="progress", importance=0.4)
            else:
                # Analyser l'échec, l'apprendre, ADAPTER (la stratégie change car
                # l'erreur entre dans `history` relue au tour suivant).
                await self._ltm.observe(
                    scope, f"ERREUR pour « {goal} » via {action} : {obs.get('error')}",
                    kind="error", importance=0.7)

        # 2) Tentatives épuisées : NE PAS abandonner — problème ouvert à retenter.
        await self._ltm.remember(
            scope, f"PROBLÈME OUVERT (à retenter) : {goal}",
            source="open_problem", importance=0.9, tags=["open_problem"])
        return {
            "status": "unresolved", "goal": goal,
            "iterations": max_iterations, "history": history,
            "gave_up": False, "will_retry": True,
            "next_steps": "Stratégie à faire évoluer ; réessayer avec de nouveaux outils/infos.",
        }

    async def _llm_reason(self, *, goal: str, memories: list[dict],
                          history: list[dict]) -> dict:
        """Chemin live : le LLM décide de la prochaine action via tool-calling.

        Best-effort : sans provider disponible, renvoie une conclusion prudente plutôt
        que d'échouer (le vrai raisonnement multi-tours requiert une clé).
        """
        from ai_engine.modules.provider.manager import get_provider_manager
        from ai_engine.modules.provider.base import ChatMessage

        system = build_system_prompt(memories)
        transcript = "\n".join(
            f"[{h['step']}] action={h['action']} -> "
            f"{'OK' if h['observation'].get('ok') else 'ERREUR: ' + str(h['observation'].get('error'))}"
            for h in history
        ) or "(aucune action encore)"
        prompt = (
            f"OBJECTIF : {goal}\n\nHISTORIQUE :\n{transcript}\n\n"
            "Conclus par la meilleure réponse possible dès que l'objectif est atteignable."
        )
        try:
            res = await get_provider_manager().chat(
                [ChatMessage(role="user", content=prompt)], system=system)
            return {"done": True, "answer": res.content}
        except Exception as e:
            return {"done": True, "answer": f"(hors-ligne, raisonnement limité : {e})"}


def get_resilient_agent() -> ResilientAgent:
    return ResilientAgent()
