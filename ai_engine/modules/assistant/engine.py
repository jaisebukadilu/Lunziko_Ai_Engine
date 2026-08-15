"""AppAssistant — assistant scopé à une application Lunziko + pool d'agents (≤ 5).

Scope = zone de compétence de l'app (fonctions issues du registre écosystème). L'assistant
raisonne dans ce périmètre (contexte app + mémoire + activité), signale et redirige les
demandes hors périmètre, et peut déléguer à des agents spécialisés (max 5 par app).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai_engine.modules.assistant import MAX_AGENTS_PER_APP
from ai_engine.core.registry import get_storage
from ai_engine.modules.activity.engine import get_activity_engine
from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
from ai_engine.modules.memory.engine import get_memory_engine
from ai_engine.modules.provider.base import ChatMessage, ProviderError
from ai_engine.modules.provider.manager import get_provider_manager

# Score écosystème au-delà duquel une requête est jugée « mieux servie par une autre app ».
_OUT_OF_SCOPE_MARGIN = 0.08


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AppAssistant:
    def __init__(self) -> None:
        self._store = get_storage()
        self._eco = get_ecosystem_engine()

    @staticmethod
    def _ns_agents(app: str) -> str:
        return f"assistant_agents:{app}"

    # --- Scope (zone de compétence) ---------------------------------------
    def scope(self, app: str) -> dict:
        rec = self._eco.get_app(app)
        if rec is None:
            return {"app": app, "known": False,
                    "competence": [], "category": "", "exposes": "", "consumes": "",
                    "note": "application non répertoriée ; assistant générique Lunziko"}
        return {
            "app": rec["slug"], "name": rec["name"], "known": True,
            "category": rec.get("category", ""),
            "competence": rec.get("functions", []),
            "exposes": rec.get("exposes", ""),
            "consumes": rec.get("consumes", ""),
            "is_aggregator": rec.get("is_aggregator", False),
        }

    def _system_prompt(self, sc: dict) -> str:
        name = sc.get("name", sc["app"])
        lines = [
            f"Tu es l'assistant IA intégré à **{name}** dans l'écosystème Lunziko.",
            "Tu peux tout faire, tout corriger et assister l'utilisateur — MAIS strictement dans "
            "la ZONE DE COMPÉTENCE de cette application.",
        ]
        if sc.get("competence"):
            comp = "; ".join(sc["competence"][:12])
            lines.append(f"Zone de compétence de {name} : {comp}.")
        lines.append(
            "Si la demande sort de ce périmètre, dis-le clairement et oriente vers l'application "
            "Lunziko compétente, sans inventer. Reste concis, fiable et actionnable."
        )
        return "\n".join(lines)

    async def _out_of_scope(self, app: str, query: str) -> dict | None:
        """Détecte si une AUTRE app sert nettement mieux la requête (garde de périmètre)."""
        try:
            hits = await self._eco.search(query, 3)
        except Exception:
            return None
        if not hits:
            return None
        top = hits[0]
        if top["slug"] != app and top["score"] >= _OUT_OF_SCOPE_MARGIN:
            same = next((h for h in hits if h["slug"] == app), None)
            if same is None or top["score"] - same["score"] >= _OUT_OF_SCOPE_MARGIN:
                return {"redirect_to": top["slug"], "redirect_name": top.get("name", top["slug"]),
                        "score": top["score"]}
        return None

    # --- Assistance -------------------------------------------------------
    async def ask(
        self, app: str, query: str, *, user_id: str | None = None,
        provider: str | None = None, max_tokens: int = 1024,
    ) -> dict:
        sc = self.scope(app)
        redirect = await self._out_of_scope(app, query)

        context: list[str] = []
        if user_id:
            for m in await get_memory_engine().recall(user_id, query, 3):
                context.append(f"[mémoire] {m['key']}: {m['value']}")
            for a in get_activity_engine().timeline(user_id, limit=4):
                context.append(f"[activité] {a['app']}/{a['action']}"
                               + (f" → {a['target']}" if a['target'] else ""))

        system = self._system_prompt(sc)
        if redirect:
            system += (f"\n\nNOTE : cette demande relève plutôt de « {redirect['redirect_name']} ». "
                       "Aide si c'est dans ton périmètre, sinon oriente l'utilisateur.")
        if context:
            system += "\n\nCONTEXTE:\n" + "\n".join(context)

        answer = None
        error = None
        try:
            res = await get_provider_manager().chat(
                [ChatMessage(role="user", content=query)],
                provider=provider, system=system, max_tokens=max_tokens,
            )
            answer = {"content": res.content, "provider": res.provider, "model": res.model}
        except ProviderError as e:
            error = str(e)

        return {
            "app": sc["app"], "scope_known": sc["known"],
            "in_scope": redirect is None, "redirect": redirect,
            "answer": answer, "error": error,
        }

    # --- Agents (≤ 5 par application) -------------------------------------
    def list_agents(self, app: str) -> list[dict]:
        return sorted(self._store.list(self._ns_agents(app)), key=lambda a: a.get("created_at", ""))

    def create_agent(self, app: str, role: str, description: str = "") -> dict:
        agents = self.list_agents(app)
        if any(a["role"].lower() == role.lower() for a in agents):
            raise ValueError(f"un agent « {role} » existe déjà pour {app}")
        if len(agents) >= MAX_AGENTS_PER_APP:
            raise ValueError(f"limite atteinte : {MAX_AGENTS_PER_APP} agents maximum par application")
        aid = uuid.uuid4().hex[:12]
        rec = {"id": aid, "app": app, "role": role, "description": description, "created_at": _now()}
        self._store.put(self._ns_agents(app), aid, rec)
        return rec

    def delete_agent(self, app: str, agent_id: str) -> bool:
        return self._store.delete(self._ns_agents(app), agent_id)

    async def team_run(
        self, app: str, task: str, *, user_id: str | None = None,
        provider: str | None = None, max_tokens: int = 512,
    ) -> dict:
        """Répartit une tâche sur les agents de l'app (max 5) pour fluidifier le travail."""
        sc = self.scope(app)
        agents = self.list_agents(app)
        if not agents:
            # sans agents déclarés : réponse directe de l'assistant
            direct = await self.ask(app, task, user_id=user_id, provider=provider, max_tokens=max_tokens)
            return {"app": app, "agents_used": 0, "results": [], "assistant": direct}

        results = []
        base = self._system_prompt(sc)
        for ag in agents[:MAX_AGENTS_PER_APP]:
            sub_system = (base + f"\n\nTON RÔLE dans l'équipe : {ag['role']}."
                          + (f" {ag['description']}" if ag['description'] else "")
                          + " Traite uniquement la part de la tâche qui relève de ton rôle.")
            try:
                res = await get_provider_manager().chat(
                    [ChatMessage(role="user", content=task)],
                    provider=provider, system=sub_system, max_tokens=max_tokens,
                )
                results.append({"agent": ag["role"], "content": res.content, "provider": res.provider})
            except ProviderError as e:
                results.append({"agent": ag["role"], "error": str(e)})
        return {"app": app, "agents_used": len(results), "results": results}


def get_app_assistant() -> AppAssistant:
    return AppAssistant()
