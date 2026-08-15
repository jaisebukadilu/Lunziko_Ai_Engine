"""ContextAssembler (A-15) — assemble un contexte unifié pour l'IA d'application.

Agrège, pour une requête : profil + habitudes + activité récente + état applicatif live +
connaissance (knowledge/RAG) + app écosystème pertinente, sous **budget** et **temporel/spatial**.
Renvoie une structure exploitable + un bloc `system` prêt à injecter dans un agent.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.modules.activity.engine import get_activity_engine
from ai_engine.modules.context.appstate import get_appstate_store
from ai_engine.modules.context.profile import get_profile_store


def _temporal(timezone_name: str | None) -> dict:
    now = datetime.now(timezone.utc)
    hour = now.hour
    moment = ("nuit" if hour < 6 else "matin" if hour < 12
              else "après-midi" if hour < 18 else "soir")
    return {"utc": now.isoformat(), "hour_utc": hour, "moment": moment,
            "timezone": timezone_name or "UTC"}


class ContextAssembler:
    async def assemble(
        self, user_id: str, *, query: str = "", app: str | None = None,
        timezone_name: str | None = None, location: str | None = None,
        max_activity: int = 5, max_knowledge: int = 3, budget_chars: int = 4000,
    ) -> dict:
        prof = get_profile_store()
        profile = prof.get(user_id)
        habits = prof.habits(user_id)
        activity = get_activity_engine().timeline(user_id, limit=max_activity)
        appstate = get_appstate_store().get(user_id, app) if app else get_appstate_store().get(user_id)

        knowledge = []
        if query:
            try:
                knowledge = await get_activity_engine().search(user_id, query, max_knowledge)
            except Exception:
                knowledge = []

        eco_app = None
        if app:
            try:
                from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
                rec = get_ecosystem_engine().get_app(app)
                if rec:
                    eco_app = {"name": rec["name"], "competence": rec.get("functions", [])[:8]}
            except Exception:
                eco_app = None

        temporal = _temporal(timezone_name)
        if location:
            temporal["location"] = location

        ctx = {
            "user_id": user_id,
            "temporal": temporal,
            "profile": {"role": profile.get("role", ""), "language": profile.get("language", ""),
                        "preferences": profile.get("preferences", {})},
            "habits": habits,
            "recent_activity": [
                {"app": a["app"], "action": a["action"], "target": a.get("target", ""),
                 "status": a.get("status", "ok")} for a in activity
            ],
            "app_state": appstate,
            "app_scope": eco_app,
            "related_activity": [{"app": k["app"], "action": k["action"]} for k in knowledge],
        }
        ctx["system_block"] = self._system_block(ctx)[:budget_chars]
        return ctx

    @staticmethod
    def _system_block(ctx: dict) -> str:
        lines = ["CONTEXTE UTILISATEUR (temps réel) :"]
        t = ctx["temporal"]
        lines.append(f"- Moment : {t['moment']} ({t['hour_utc']}h UTC, {t['timezone']})"
                     + (f", lieu : {t['location']}" if t.get("location") else ""))
        p = ctx["profile"]
        if p["role"] or p["language"]:
            lines.append(f"- Profil : rôle={p['role'] or '—'}, langue={p['language'] or '—'}")
        if ctx["habits"]["top_apps"]:
            apps = ", ".join(f"{a['app']}" for a in ctx["habits"]["top_apps"][:3])
            lines.append(f"- Apps les plus utilisées : {apps}")
        if ctx["recent_activity"]:
            acts = "; ".join(f"{a['app']}/{a['action']}"
                             + (" [erreur]" if a["status"] == "error" else "")
                             for a in ctx["recent_activity"])
            lines.append(f"- Actions récentes : {acts}")
        if ctx["app_state"]:
            st = ctx["app_state"]
            st = st if isinstance(st, dict) else (st[0] if st else None)
            if st:
                bits = []
                if st.get("screen"):
                    bits.append(f"écran={st['screen']}")
                if st.get("last_error"):
                    bits.append(f"erreur={st['last_error']}")
                if st.get("form_draft"):
                    bits.append("formulaire en cours")
                if bits:
                    lines.append(f"- État applicatif : {', '.join(bits)}")
        if ctx["app_scope"]:
            lines.append(f"- App courante : {ctx['app_scope']['name']} "
                         f"(compétences : {'; '.join(ctx['app_scope']['competence'][:4])})")
        return "\n".join(lines)


def get_context_assembler() -> ContextAssembler:
    return ContextAssembler()
