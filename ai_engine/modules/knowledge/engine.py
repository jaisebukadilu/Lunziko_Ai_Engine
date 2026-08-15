"""KnowledgeEngine — items typés + relations auto-liées par similarité, sur les ports.

Ajout d'un item : persistance (StoragePort) + indexation (VectorPort) + création
automatique de relations vers les items proches (cosinus ≥ seuil). Recherche sémantique.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager

ItemType = Literal[
    "fact", "concept", "person", "organization", "project", "document",
    "meeting", "decision", "task", "note", "idea", "reference", "event",
]

LINK_THRESHOLD = 0.30  # seuil cosinus d'auto-linking (cf. audit)


class KnowledgeEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()

    @staticmethod
    def _ns_item(org: str) -> str:
        return f"knowledge:{org}"

    @staticmethod
    def _ns_rel(org: str) -> str:
        return f"knowledge_rel:{org}"

    async def add(
        self, org: str, item_type: str, title: str, content: str, tags: list[str] | None = None
    ) -> dict:
        kid = uuid.uuid4().hex
        rec = {
            "id": kid,
            "type": item_type,
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        ns, ns_rel = self._ns_item(org), self._ns_rel(org)
        self._store.put(ns, kid, rec)
        vector = (await self._emb.embed([f"{title}\n{content}"])).vectors[0]
        # auto-linking AVANT insertion du nouveau vecteur (évite l'auto-relation)
        links: list[dict] = []
        for hit in self._vec.search(ns, vector, 6):
            if hit["score"] >= LINK_THRESHOLD:
                rel_id = f"{kid}~{hit['id']}"
                rel = {"id": rel_id, "source": kid, "target": hit["id"], "score": round(hit["score"], 4)}
                self._store.put(ns_rel, rel_id, rel)
                links.append(rel)
        self._vec.upsert(ns, kid, vector, {"kid": kid})
        return {"id": kid, "type": item_type, "title": title, "auto_links": links}

    async def search(self, org: str, query: str, k: int = 5) -> list[dict]:
        ns = self._ns_item(org)
        qvec = (await self._emb.embed([query])).vectors[0]
        out: list[dict] = []
        for hit in self._vec.search(ns, qvec, k):
            rec = self._store.get(ns, hit["id"])
            if rec:
                out.append({**rec, "score": round(hit["score"], 4)})
        return out

    def relations(self, org: str, kid: str) -> list[dict]:
        return [
            r for r in self._store.list(self._ns_rel(org))
            if r.get("source") == kid or r.get("target") == kid
        ]

    def get(self, org: str, kid: str) -> dict | None:
        return self._store.get(self._ns_item(org), kid)


def get_knowledge_engine() -> KnowledgeEngine:
    return KnowledgeEngine()
