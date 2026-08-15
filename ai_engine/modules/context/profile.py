"""Profil & habitudes (A-14).

Cache de profil local (rôle, langue, préférences) + **habitudes dérivées de l'activité**
(apps les plus utilisées, heures actives). L'identité/RBAC restent l'autorité de Platform :
ce module n'est qu'un cache comportemental, il ne valide aucun droit.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage
from ai_engine.modules.activity.engine import get_activity_engine

NS = "profile"


class ProfileStore:
    def __init__(self) -> None:
        self._store = get_storage()

    def get(self, user_id: str) -> dict:
        rec = self._store.get(NS, user_id)
        return rec or {"id": user_id, "role": "", "language": "", "preferences": {}}

    def set(self, user_id: str, *, role: str | None = None, language: str | None = None,
            preferences: dict | None = None) -> dict:
        rec = self.get(user_id)
        rec["id"] = user_id
        if role is not None:
            rec["role"] = role
        if language is not None:
            rec["language"] = language
        if preferences is not None:
            rec["preferences"] = {**rec.get("preferences", {}), **preferences}
        rec["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._store.put(NS, user_id, rec)
        return rec

    def habits(self, user_id: str, *, sample: int = 100) -> dict:
        """Habitudes calculées depuis le journal d'activité (non déclaratives)."""
        rows = get_activity_engine().timeline(user_id, limit=sample)
        per_app: dict[str, int] = {}
        hours: dict[int, int] = {}
        for r in rows:
            per_app[r["app"]] = per_app.get(r["app"], 0) + 1
            ts = r.get("ts") or ""
            if len(ts) >= 13 and ts[11:13].isdigit():
                h = int(ts[11:13])
                hours[h] = hours.get(h, 0) + 1
        top_apps = sorted(per_app.items(), key=lambda kv: kv[1], reverse=True)[:5]
        active_hours = sorted(hours.items(), key=lambda kv: kv[1], reverse=True)[:3]
        return {
            "events": len(rows),
            "top_apps": [{"app": a, "count": c} for a, c in top_apps],
            "active_hours": [h for h, _ in active_hours],
        }


def get_profile_store() -> ProfileStore:
    return ProfileStore()
