"""AI Blackboard — espace de travail partagé (état de tâche).

Tous les Brains/agents travaillent sur le MÊME état : objectif, contexte, plan, artefacts,
décisions, sorties, erreurs, validation. Persisté (StoragePort). Évite de tout régénérer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

NS = "blackboard"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Blackboard:
    def __init__(self) -> None:
        self._store = get_storage()

    def create(self, goal: str, *, user_id: str | None = None, app: str | None = None) -> dict:
        tid = uuid.uuid4().hex
        rec = {"id": tid, "goal": goal, "user_id": user_id, "app": app,
               "status": "open", "context": {}, "plan": [], "artifacts": [],
               "decisions": [], "outputs": [], "errors": [], "validation": [],
               "created_at": _now(), "updated_at": _now()}
        self._store.put(NS, tid, rec)
        return rec

    def get(self, tid: str) -> dict | None:
        return self._store.get(NS, tid)

    def update(self, tid: str, **fields) -> dict | None:
        rec = self._store.get(NS, tid)
        if rec is None:
            return None
        for k, v in fields.items():
            if k in ("context",) and isinstance(v, dict):
                rec[k] = {**rec.get(k, {}), **v}
            else:
                rec[k] = v
        rec["updated_at"] = _now()
        self._store.put(NS, tid, rec)
        return rec

    def append(self, tid: str, field: str, value) -> dict | None:
        rec = self._store.get(NS, tid)
        if rec is None or field not in ("artifacts", "decisions", "outputs", "errors", "validation", "plan"):
            return None
        rec.setdefault(field, []).append(value)
        rec["updated_at"] = _now()
        self._store.put(NS, tid, rec)
        return rec

    def list(self, limit: int = 20) -> list[dict]:
        rows = sorted(self._store.list(NS), key=lambda r: r.get("updated_at", ""), reverse=True)
        return [{"id": r["id"], "goal": r["goal"], "status": r["status"],
                 "updated_at": r["updated_at"]} for r in rows[:limit]]


def get_blackboard() -> Blackboard:
    return Blackboard()
