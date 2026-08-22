"""ReasoningEngine — stratégies de raisonnement avancées, provider-agnostiques.

Chaque stratégie orchestre des appels LLM (réimplémentation clean-room de techniques OSS).
`chat_fn` est injectable (tests offline) ; par défaut = Provider Manager de l'AI Engine, donc
fonctionne aussi bien avec le LLM natif `lunziko`, Ollama local ou un provider cloud.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Awaitable, Callable

from ai_engine.modules.provider.base import ChatMessage

ChatFn = Callable[..., Awaitable[object]]

_FINAL_RE = re.compile(r"(?:r[ée]ponse|answer|final)\s*[:\-]\s*(.+)", re.IGNORECASE)


def _extract_final(text: str) -> str:
    """Extrait la réponse finale d'une sortie CoT (ligne 'Réponse: …' sinon dernière ligne)."""
    matches = _FINAL_RE.findall(text or "")
    if matches:
        return matches[-1].strip()
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return lines[-1] if lines else ""


class ReasoningEngine:
    def __init__(self, chat_fn: ChatFn | None = None) -> None:
        self._chat_fn = chat_fn

    async def _chat(self, prompt: str, system: str | None = None, **kw) -> str:
        chat = self._chat_fn
        if chat is None:
            from ai_engine.modules.provider.manager import get_provider_manager
            chat = get_provider_manager().chat
        res = await chat([ChatMessage(role="user", content=prompt)], system=system, **kw)
        return getattr(res, "content", None) or str(res)

    # --- Chain-of-Thought ------------------------------------------------
    async def cot(self, question: str) -> dict:
        system = ("Raisonne étape par étape, puis conclus par une ligne « Réponse: <réponse finale> ».")
        out = await self._chat(question, system=system)
        return {"strategy": "chain_of_thought", "reasoning": out, "answer": _extract_final(out)}

    # --- Self-Consistency (vote majoritaire) ----------------------------
    async def self_consistency(self, question: str, n: int = 5) -> dict:
        system = "Raisonne étape par étape puis termine par « Réponse: <réponse> »."
        answers: list[str] = []
        samples: list[str] = []
        for _ in range(max(1, n)):
            out = await self._chat(question, system=system)
            samples.append(out)
            answers.append(_extract_final(out).lower())
        counts = Counter(a for a in answers if a)
        winner, votes = (counts.most_common(1)[0] if counts else ("", 0))
        return {
            "strategy": "self_consistency", "n": n, "answer": winner,
            "votes": votes, "distribution": dict(counts), "samples": samples,
        }

    # --- Reflexion (auto-critique + révision) ---------------------------
    async def reflexion(self, question: str) -> dict:
        draft = await self._chat(question, system="Réponds au mieux à la demande.")
        critique = await self._chat(
            f"DEMANDE:\n{question}\n\nRÉPONSE PROPOSÉE:\n{draft}\n\n"
            "Critique cette réponse : erreurs, omissions, imprécisions. Sois concis et concret.",
            system="Tu es un relecteur critique et exigeant.")
        revised = await self._chat(
            f"DEMANDE:\n{question}\n\nRÉPONSE INITIALE:\n{draft}\n\nCRITIQUE:\n{critique}\n\n"
            "Produis une réponse RÉVISÉE qui corrige les points soulevés.",
            system="Améliore la réponse en tenant compte de la critique.")
        return {"strategy": "reflexion", "draft": draft, "critique": critique, "answer": revised}

    # --- Plan-and-Solve --------------------------------------------------
    async def plan_and_solve(self, question: str) -> dict:
        plan = await self._chat(
            question, system="Établis d'abord un PLAN numéroté pour résoudre la demande (sans la résoudre).")
        solution = await self._chat(
            f"DEMANDE:\n{question}\n\nPLAN:\n{plan}\n\nExécute le plan et donne la réponse finale.",
            system="Suis le plan étape par étape.")
        return {"strategy": "plan_and_solve", "plan": plan, "answer": solution}

    # --- Step-Back -------------------------------------------------------
    async def step_back(self, question: str) -> dict:
        principle = await self._chat(
            question, system="Quel est le PRINCIPE ou concept général sous-jacent à cette question ? "
                             "Énonce-le d'abord, sans répondre au cas précis.")
        answer = await self._chat(
            f"PRINCIPE:\n{principle}\n\nQUESTION:\n{question}\n\nApplique le principe pour répondre.",
            system="Applique le principe général au cas particulier.")
        return {"strategy": "step_back", "principle": principle, "answer": answer}

    # --- Tree-of-Thoughts (breadth + évaluation) ------------------------
    async def tree_of_thoughts(self, question: str, breadth: int = 3) -> dict:
        branches: list[str] = []
        for i in range(max(2, breadth)):
            b = await self._chat(
                f"{question}\n\n(Propose l'APPROCHE #{i+1}, distincte des autres, pour résoudre — "
                "esquisse seulement.)",
                system="Génère une approche candidate, concise.")
            branches.append(b)
        # Évaluation : demander un choix argumenté de la meilleure approche.
        listing = "\n".join(f"[{i+1}] {b}" for i, b in enumerate(branches))
        pick = await self._chat(
            f"QUESTION:\n{question}\n\nAPPROCHES:\n{listing}\n\n"
            "Indique le numéro de la MEILLEURE approche puis développe-la jusqu'à la réponse finale "
            "(termine par « Réponse: … »).",
            system="Évalue les approches et développe la meilleure.")
        return {"strategy": "tree_of_thoughts", "branches": branches,
                "answer": _extract_final(pick), "development": pick}

    # --- Sélection automatique ------------------------------------------
    def _auto_strategy(self, question: str) -> str:
        low = question.lower()
        if any(k in low for k in ("calcul", "combien", "=", "somme", "probabilit", "équation")):
            return "self_consistency"
        if any(k in low for k in ("plan", "étapes", "conçois", "construis", "implémente")):
            return "plan_and_solve"
        if any(k in low for k in ("améliore", "corrige", "rédige", "écris", "relis")):
            return "reflexion"
        if any(k in low for k in ("pourquoi", "explique", "principe", "concept")):
            return "step_back"
        return "chain_of_thought"

    async def reason(self, question: str, strategy: str = "auto", **kw) -> dict:
        strat = self._auto_strategy(question) if strategy == "auto" else strategy
        dispatch = {
            "chain_of_thought": lambda: self.cot(question),
            "self_consistency": lambda: self.self_consistency(question, int(kw.get("n", 5))),
            "reflexion": lambda: self.reflexion(question),
            "plan_and_solve": lambda: self.plan_and_solve(question),
            "step_back": lambda: self.step_back(question),
            "tree_of_thoughts": lambda: self.tree_of_thoughts(question, int(kw.get("breadth", 3))),
        }
        if strat not in dispatch:
            raise ValueError(f"stratégie inconnue : {strat}")
        result = await dispatch[strat]()
        result["selected_strategy"] = strat
        return result


def get_reasoning_engine() -> ReasoningEngine:
    return ReasoningEngine()
