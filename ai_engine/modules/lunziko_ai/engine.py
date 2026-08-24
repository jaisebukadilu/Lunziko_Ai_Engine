"""LunzikoAssistant — assistant conversationnel intégré à 5 piliers.

1. GRAND MODÈLE        : Provider Manager (qwen2.5:7b par défaut ; `ollama-mistral` = 2e modèle)
2. CONNAISSANCE        : module `ecosystem` (registre indexé au démarrage) -> faits Lunziko exacts
3. MÉMOIRE PERSISTANTE : module `learning` (append-only, n'oublie jamais)
4. APPRENTISSAGE CONT. : learning.observe à chaque échange
5. RECHERCHE WEB       : module `search` (DuckDuckGo sans clé)

Réutilise les modules existants sans les modifier. 100 % local (sauf web).
"""

from __future__ import annotations

from ai_engine.modules.learning.engine import get_continuous_memory
from ai_engine.modules.provider.base import ChatMessage
from ai_engine.modules.provider.manager import get_provider_manager

WEB_TRIGGERS = ("cherche", "internet", "web", "actualité", "actu", "aujourd'hui", "météo",
                "récent", "dernière", "news", "prix", "cours", "en ligne", "google")


class LunzikoAssistant:
    def __init__(self) -> None:
        self._ltm = get_continuous_memory()
        self._pm = get_provider_manager()

    async def _knowledge(self, query: str) -> str:
        """Faits Lunziko via la connaissance écosystème indexée."""
        try:
            from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
            hits = await get_ecosystem_engine().search(query, 3)
        except Exception:
            return ""
        out = []
        for h in hits:
            if h.get("score", 0) < 0.2:
                continue
            fns = ", ".join(h.get("functions", [])[:8])
            out.append(f"{h.get('name')} — {h.get('category','')}. Fonctions: {fns}. "
                       f"Expose: {h.get('exposes','')}. Consomme: {h.get('consumes','')}.")
        return "\n".join(out)

    async def _web(self, query: str) -> str:
        try:
            from ai_engine.modules.search.engine import get_search_engine
            res = await get_search_engine().search(query, k=3)
            items = res.get("results", []) if isinstance(res, dict) else res
            return "\n".join(f"- {r.get('title','')}: {r.get('snippet','')} ({r.get('url','')})"
                             for r in items[:3])
        except Exception as e:
            return f"(recherche web indisponible: {e})"

    async def chat(self, user: str, *, scope: str = "global", provider: str | None = None,
                   use_web: bool | None = None, learn: bool = True) -> dict:
        # 2. MÉMOIRE PERSISTANTE — rappel avant d'agir
        mem = await self._ltm.recall(scope, user, k=3)
        mem_ctx = "\n".join(f"- {x['text']}" for x in mem) if mem else "(aucun souvenir)"
        # 2. CONNAISSANCE Lunziko
        kb = await self._knowledge(user)
        # 5. RECHERCHE WEB
        if use_web is None:
            use_web = any(t in user.lower() for t in WEB_TRIGGERS)
        web = await self._web(user) if use_web else ""

        system = (
            "Tu es Lunziko AI, l'assistant conversationnel de l'écosystème Lunziko. Réponds de "
            "façon naturelle et EXACTE en t'appuyant sur la CONNAISSANCE et la MÉMOIRE ; n'invente "
            "pas de faits Lunziko. Suis les instructions de l'utilisateur.\n\n"
            f"MÉMOIRE de l'utilisateur:\n{mem_ctx}\n\n"
            f"CONNAISSANCE LUNZIKO:\n{kb or '(aucune correspondance)'}"
            + (f"\n\nRÉSULTATS WEB:\n{web}" if web else ""))

        res = await self._pm.chat([ChatMessage(role="user", content=user)],
                                  provider=provider, system=system, max_tokens=400)
        # 4. APPRENTISSAGE CONTINU
        if learn:
            await self._ltm.observe(scope, f"Question: {user}", kind="dialogue")
        return {
            "answer": res.content.strip(),
            "model": res.model, "provider": res.provider,
            "used": {"memory": bool(mem), "knowledge": bool(kb), "web": bool(web)},
        }

    async def remember(self, scope: str, fact: str, importance: float = 0.8) -> dict:
        return await self._ltm.remember(scope, fact, importance=importance)


def get_lunziko_assistant() -> LunzikoAssistant:
    return LunzikoAssistant()
