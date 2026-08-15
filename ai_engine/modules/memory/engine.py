"""MemoryEngine — mémoire utilisateur chiffrée + rappel sémantique, sur les ports.

Valeurs chiffrées via `crypto` avant persistance (StoragePort). Un embedding de
« clé: valeur » est indexé (VectorPort) pour le rappel par similarité — offline via le
repli hash. Aucune dépendance à Platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.memory.crypto import get_cipher

Category = Literal["preferences", "habits", "facts", "projects", "contacts", "general"]


class MemoryEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()
        self._cipher = get_cipher()

    @staticmethod
    def _ns(user_id: str) -> str:
        return f"memory:{user_id}"

    def _reveal(self, rec: dict) -> dict:
        return {
            "id": rec["id"],
            "category": rec.get("category", "general"),
            "key": rec.get("key", ""),
            "value": self._cipher.decrypt(rec["enc"]),
            "created_at": rec.get("created_at"),
        }

    async def save(self, user_id: str, category: str, key: str, value: str) -> str:
        mid = uuid.uuid4().hex
        rec = {
            "id": mid,
            "category": category,
            "key": key,
            "enc": self._cipher.encrypt(value),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        ns = self._ns(user_id)
        self._store.put(ns, mid, rec)
        vector = (await self._emb.embed([f"{key}: {value}"])).vectors[0]
        self._vec.upsert(ns, mid, vector, {"mid": mid})
        return mid

    def list(self, user_id: str) -> list[dict]:
        return [self._reveal(r) for r in self._store.list(self._ns(user_id))]

    async def recall(self, user_id: str, query: str, k: int = 5) -> list[dict]:
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

    def delete(self, user_id: str, mid: str) -> bool:
        ns = self._ns(user_id)
        self._vec.delete(ns, mid)
        return self._store.delete(ns, mid)


def get_memory_engine() -> MemoryEngine:
    return MemoryEngine()
