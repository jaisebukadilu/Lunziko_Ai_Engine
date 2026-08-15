"""AppState — état applicatif live, éphémère (A-16).

Écran courant, brouillon de formulaire, dernière erreur : capté pour le raisonnement, pas
rejoué (pas de session-replay). TTL court ; minimisation. Sur StoragePort (ns par utilisateur).
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

DEFAULT_TTL = 900  # 15 min


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AppStateStore:
    def __init__(self) -> None:
        self._store = get_storage()

    @staticmethod
    def _ns(user_id: str) -> str:
        return f"appstate:{user_id}"

    def put(self, user_id: str, app: str, *, screen: str = "", form_draft: dict | None = None,
            last_error: str = "", ttl: int = DEFAULT_TTL) -> dict:
        rec = {
            "id": app,
            "app": app,
            "screen": screen,
            "form_draft": form_draft or {},
            "last_error": last_error,
            "updated_at": _now().isoformat(),
            "expires_at": (_now().timestamp() + ttl),
        }
        self._store.put(self._ns(user_id), app, rec)
        return {"app": app, "expires_in": ttl}

    def get(self, user_id: str, app: str | None = None) -> dict | list | None:
        ns = self._ns(user_id)
        if app is not None:
            rec = self._store.get(ns, app)
            return self._fresh(ns, rec)
        out = []
        for rec in self._store.list(ns):
            fresh = self._fresh(ns, rec)
            if fresh:
                out.append(fresh)
        return out

    def _fresh(self, ns: str, rec: dict | None) -> dict | None:
        if not rec:
            return None
        if rec.get("expires_at", 0) < _now().timestamp():
            self._store.delete(ns, rec["id"])  # purge à la lecture
            return None
        return {k: v for k, v in rec.items() if k != "expires_at"}


def get_appstate_store() -> AppStateStore:
    return AppStateStore()
