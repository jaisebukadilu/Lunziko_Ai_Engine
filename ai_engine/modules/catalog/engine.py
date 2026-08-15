"""CatalogEngine — registre de schémas de données + résolution sémantique.

Un schéma = {app, dataset, fields:{nom: type}, description}. Persisté (StoragePort) et indexé
(VectorPort) pour retrouver le schéma pertinent à partir d'une question en langage naturel.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager

NS = "catalog"


def _sid(app: str, dataset: str) -> str:
    return f"{app}:{dataset}".lower().replace(" ", "-")


class CatalogEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()

    @staticmethod
    def _searchable(rec: dict) -> str:
        fields = " ".join(f"{k}:{v}" for k, v in rec.get("fields", {}).items())
        return f"{rec['app']} {rec['dataset']} {rec.get('description','')} {fields}"

    async def register(self, app: str, dataset: str, fields: dict,
                       description: str = "") -> dict:
        sid = _sid(app, dataset)
        rec = {"id": sid, "app": app, "dataset": dataset, "fields": fields,
               "description": description, "updated_at": datetime.now(timezone.utc).isoformat()}
        self._store.put(NS, sid, rec)
        vector = (await self._emb.embed([self._searchable(rec)])).vectors[0]
        self._vec.upsert(NS, sid, vector, {"sid": sid})
        return {"id": sid, "fields": len(fields)}

    def list(self, app: str | None = None) -> list[dict]:
        rows = self._store.list(NS)
        if app:
            rows = [r for r in rows if r.get("app") == app]
        return sorted(rows, key=lambda r: r.get("id", ""))

    def get(self, sid: str) -> dict | None:
        return self._store.get(NS, sid)

    async def resolve(self, query: str, k: int = 3) -> list[dict]:
        qvec = (await self._emb.embed([query])).vectors[0]
        out = []
        for hit in self._vec.search(NS, qvec, k):
            rec = self._store.get(NS, hit["id"])
            if rec:
                out.append({**rec, "score": round(hit["score"], 4)})
        return out


def get_catalog_engine() -> CatalogEngine:
    return CatalogEngine()
