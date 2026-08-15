"""ConnectorEngine — ingestion multi-sources + recherche unifiée cross-namespace.

Types de connecteurs (source) : document, chat, email, file, note, web. Chaque item est
indexé dans le RAG avec sa source. La recherche unifiée interroge plusieurs namespaces et
fusionne les résultats par score, avec attribution de source.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_engine.core.registry import get_storage
from ai_engine.modules.rag.service import get_rag_service

NS_REG = "connector_registry"

CONNECTOR_TYPES = ["document", "chat", "email", "file", "note", "web"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectorEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._rag = get_rag_service()

    async def ingest(self, connector: str, namespace: str, items: list[dict]) -> dict:
        if connector not in CONNECTOR_TYPES:
            raise ValueError(f"connecteur inconnu: {connector} (attendus: {', '.join(CONNECTOR_TYPES)})")
        indexed = 0
        for i, item in enumerate(items):
            text = item.get("text") or item.get("content") or ""
            if not text.strip():
                continue
            doc_id = str(item.get("id") or f"{connector}-{i}")
            meta = {"source": connector, "title": item.get("title", ""), **(item.get("meta") or {})}
            indexed += await self._rag.index(namespace, doc_id, text, meta)
        # registre des namespaces alimentés (pour la recherche unifiée "toutes sources")
        rec = self._store.get(NS_REG, namespace) or {"id": namespace, "connectors": [], "docs": 0}
        rec["connectors"] = sorted(set(rec.get("connectors", []) + [connector]))
        rec["docs"] = rec.get("docs", 0) + len(items)
        rec["updated_at"] = _now()
        self._store.put(NS_REG, namespace, rec)
        return {"connector": connector, "namespace": namespace,
                "documents": len(items), "chunks_indexed": indexed}

    def namespaces(self) -> list[dict]:
        return sorted(self._store.list(NS_REG), key=lambda r: r.get("id", ""))

    async def unified_search(self, query: str, *, namespaces: list[str] | None = None,
                             k: int = 5) -> list[dict]:
        targets = namespaces or [r["id"] for r in self.namespaces()]
        merged: list[dict] = []
        for ns in targets:
            for hit in await self._rag.search(ns, query, k):
                merged.append({**hit, "namespace": ns,
                               "source": (hit.get("meta") or {}).get("source", "")})
        merged.sort(key=lambda h: h.get("score", 0), reverse=True)
        return merged[:k]


def get_connector_engine() -> ConnectorEngine:
    return ConnectorEngine()
