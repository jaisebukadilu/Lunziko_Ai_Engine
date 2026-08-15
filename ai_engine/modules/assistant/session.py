"""Sessions d'assistant — état conversationnel pour une future interface visuelle.

Une session lie (app, utilisateur) et conserve l'historique des messages. Persistée
(StoragePort) pour qu'un frontend puisse reprendre une conversation. Neutre vis-à-vis de l'UI.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

NS = "assistant_sessions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self) -> None:
        self._store = get_storage()

    def create(self, app: str, user_id: str | None = None, title: str = "") -> dict:
        sid = uuid.uuid4().hex
        rec = {"id": sid, "app": app, "user_id": user_id, "title": title or f"Assistant {app}",
               "messages": [], "created_at": _now(), "updated_at": _now()}
        self._store.put(NS, sid, rec)
        return rec

    def get(self, sid: str) -> dict | None:
        return self._store.get(NS, sid)

    def append(self, sid: str, role: str, content: str) -> dict | None:
        rec = self._store.get(NS, sid)
        if rec is None:
            return None
        rec["messages"].append({"role": role, "content": content, "ts": _now()})
        rec["updated_at"] = _now()
        self._store.put(NS, sid, rec)
        return rec

    def list(self, app: str | None = None) -> list[dict]:
        rows = self._store.list(NS)
        if app:
            rows = [r for r in rows if r.get("app") == app]
        summary = [{"id": r["id"], "app": r["app"], "title": r["title"],
                    "messages": len(r.get("messages", [])), "updated_at": r["updated_at"]}
                   for r in rows]
        return sorted(summary, key=lambda r: r["updated_at"], reverse=True)

    def delete(self, sid: str) -> bool:
        return self._store.delete(NS, sid)


def get_session_store() -> SessionStore:
    return SessionStore()
