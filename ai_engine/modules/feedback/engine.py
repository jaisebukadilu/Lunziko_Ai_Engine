"""FeedbackEngine — enregistre les retours, calcule des stats, fournit des few-shots."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage

NS = "feedback"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FeedbackEngine:
    def __init__(self) -> None:
        self._store = get_storage()

    def record(self, *, rating: str, target_id: str = "", user_id: str | None = None,
               query: str = "", answer: str = "", correction: str = "",
               app: str | None = None) -> dict:
        if rating not in ("up", "down"):
            raise ValueError("rating doit être 'up' ou 'down'")
        fid = uuid.uuid4().hex
        rec = {"id": fid, "rating": rating, "target_id": target_id, "user_id": user_id,
               "query": query, "answer": answer, "correction": correction, "app": app,
               "created_at": _now()}
        self._store.put(NS, fid, rec)
        return {"id": fid, "rating": rating}

    def stats(self, *, app: str | None = None) -> dict:
        rows = self._store.list(NS)
        if app:
            rows = [r for r in rows if r.get("app") == app]
        up = sum(1 for r in rows if r.get("rating") == "up")
        down = sum(1 for r in rows if r.get("rating") == "down")
        corrections = sum(1 for r in rows if r.get("correction"))
        total = len(rows)
        return {"total": total, "up": up, "down": down, "corrections": corrections,
                "satisfaction": round(up / total, 3) if total else None}

    def corrections(self, *, app: str | None = None, limit: int = 10) -> list[dict]:
        """Corrections utilisateur = exemples few-shot pour améliorer les réponses futures."""
        rows = [r for r in self._store.list(NS) if r.get("correction")]
        if app:
            rows = [r for r in rows if r.get("app") == app]
        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return [{"query": r.get("query", ""), "correction": r["correction"], "app": r.get("app")}
                for r in rows[:limit]]

    def as_fewshot(self, *, app: str | None = None, limit: int = 3) -> str:
        """Bloc texte injectable dans un system prompt à partir des corrections récentes."""
        cor = self.corrections(app=app, limit=limit)
        if not cor:
            return ""
        lines = ["CORRECTIONS PASSÉES (à respecter) :"]
        for c in cor:
            q = c["query"][:80] or "(sans requête)"
            lines.append(f"- Pour « {q} » → {c['correction'][:160]}")
        return "\n".join(lines)


def get_feedback_engine() -> FeedbackEngine:
    return FeedbackEngine()
