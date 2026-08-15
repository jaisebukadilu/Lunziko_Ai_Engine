"""ActivityEngine — journal d'actions append-only + timeline + recherche + résumé.

Sur les ports existants (StoragePort + VectorPort) ; le champ libre `detail` est chiffré
via le cipher de la mémoire (AES-256-GCM si clé, sinon repli dev). Recherche sémantique via
le repli embeddings hash en hors-ligne. Aucune dépendance à Platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.memory.crypto import get_cipher
from ai_engine.modules.provider.base import ChatMessage
from ai_engine.modules.provider.manager import get_provider_manager

_SUMMARY_SYSTEM = (
    "Tu résumes l'activité récente d'un utilisateur dans une suite d'applications. "
    "Sois factuel et bref : ce qu'il a fait, sur quelles apps, points d'attention "
    "(erreurs, tâches en cours). Réponds dans la langue de la demande."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ActivityEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()
        self._cipher = get_cipher()

    @staticmethod
    def _ns(user_id: str) -> str:
        return f"activity:{user_id}"

    @staticmethod
    def _searchable(app: str, action: str, target: str, detail: str) -> str:
        return " ".join(p for p in (app, action, target, detail) if p)

    def _reveal(self, rec: dict) -> dict:
        enc = rec.get("enc_detail") or ""
        return {
            "id": rec["id"],
            "app": rec.get("app", ""),
            "action": rec.get("action", ""),
            "target": rec.get("target", ""),
            "status": rec.get("status", "ok"),
            "detail": self._cipher.decrypt(enc) if enc else "",
            "session_id": rec.get("session_id"),
            "meta": rec.get("meta", {}),
            "ts": rec.get("ts"),
        }

    async def log(
        self,
        user_id: str,
        app: str,
        action: str,
        *,
        target: str = "",
        status: str = "ok",
        detail: str = "",
        session_id: str | None = None,
        meta: dict | None = None,
        ts: str | None = None,
    ) -> dict:
        aid = uuid.uuid4().hex
        rec = {
            "id": aid,
            "app": app,
            "action": action,
            "target": target,
            "status": status,
            "enc_detail": self._cipher.encrypt(detail) if detail else "",
            "session_id": session_id,
            "meta": meta or {},
            "ts": ts or _now(),
        }
        ns = self._ns(user_id)
        self._store.put(ns, aid, rec)
        vector = (await self._emb.embed([self._searchable(app, action, target, detail)])).vectors[0]
        self._vec.upsert(ns, aid, vector, {"aid": aid, "app": app, "ts": rec["ts"]})
        return {"id": aid, "ts": rec["ts"]}

    async def log_batch(self, user_id: str, events: list[dict]) -> dict:
        ids = []
        for e in events:
            r = await self.log(
                user_id,
                e.get("app", ""),
                e.get("action", ""),
                target=e.get("target", ""),
                status=e.get("status", "ok"),
                detail=e.get("detail", ""),
                session_id=e.get("session_id"),
                meta=e.get("meta"),
                ts=e.get("ts"),
            )
            ids.append(r["id"])
        return {"logged": len(ids), "ids": ids}

    def timeline(
        self, user_id: str, *, limit: int = 20, app: str | None = None, since: str | None = None
    ) -> list[dict]:
        rows = [self._reveal(r) for r in self._store.list(self._ns(user_id))]
        if app:
            rows = [r for r in rows if r["app"] == app]
        if since:
            rows = [r for r in rows if (r["ts"] or "") >= since]
        rows.sort(key=lambda r: r["ts"] or "", reverse=True)
        return rows[:limit]

    async def search(self, user_id: str, query: str, k: int = 5) -> list[dict]:
        ns = self._ns(user_id)
        qvec = (await self._emb.embed([query])).vectors[0]
        out: list[dict] = []
        for hit in self._vec.search(ns, qvec, k):
            rec = self._store.get(ns, hit["id"])
            if rec:
                item = self._reveal(rec)
                item["score"] = round(hit["score"], 4)
                out.append(item)
        return out

    def stats(self, user_id: str, *, limit: int = 100) -> dict:
        rows = self.timeline(user_id, limit=limit)
        per_app: dict[str, int] = {}
        errors = 0
        for r in rows:
            per_app[r["app"]] = per_app.get(r["app"], 0) + 1
            if r["status"] == "error":
                errors += 1
        return {"events": len(rows), "per_app": per_app, "errors": errors}

    async def summary(
        self, user_id: str, *, limit: int = 20, provider: str | None = None, max_tokens: int = 400
    ) -> dict:
        rows = self.timeline(user_id, limit=limit)
        stats = self.stats(user_id, limit=limit)
        if not rows:
            return {"narrative": None, "stats": stats, "events": []}
        lines = [
            f"- {r['ts']} · {r['app']}/{r['action']}"
            + (f" → {r['target']}" if r["target"] else "")
            + (" [ERREUR]" if r["status"] == "error" else "")
            + (f" : {r['detail']}" if r["detail"] else "")
            for r in rows
        ]
        prompt = "Activité récente :\n" + "\n".join(lines) + "\n\nRésume."
        narrative = None
        try:  # best-effort : hors-ligne sans clé provider, on renvoie juste les stats
            answer = await get_provider_manager().chat(
                [ChatMessage(role="user", content=prompt)],
                provider=provider,
                system=_SUMMARY_SYSTEM,
                max_tokens=max_tokens,
            )
            narrative = answer.content
        except Exception:
            narrative = None
        return {"narrative": narrative, "stats": stats, "events": rows}

    def clear(self, user_id: str) -> dict:
        ns = self._ns(user_id)
        removed = 0
        for r in self._store.list(ns):
            aid = r.get("id")
            if aid:
                self._vec.delete(ns, aid)
                if self._store.delete(ns, aid):
                    removed += 1
        return {"cleared": removed}


def get_activity_engine() -> ActivityEngine:
    return ActivityEngine()
