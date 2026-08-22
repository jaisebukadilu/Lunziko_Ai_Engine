"""ContinuousMemory — mémoire long-terme (LTM) à apprentissage continu.

Principe : « apprend toujours, n'oublie jamais ».
  * APPEND-ONLY : aucune suppression dure. `archive` ne fait que marquer (tombstone),
    la ligne et son vecteur restent en base et restent rappelables sur demande.
  * RENFORCEMENT (répétition espacée) : réapprendre un fait proche NE crée pas de doublon,
    il RENFORCE l'existant (compteur + importance + fraîcheur) → la mémoire se consolide.
  * CONSOLIDATION non destructive : les quasi-doublons sont LIÉS à un canonique (le plus
    renforcé) et marqués `superseded` — jamais effacés.
  * RAPPEL pondéré : score = similarité × (1 + ln(1+renforcement)) × poids d'importance.

Construit AU-DESSUS de l'existant : StoragePort + VectorPort + chiffrement mémoire (AES-GCM),
embeddings (repli hash hors-ligne). 100 % local, indépendant de Platform.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.memory.crypto import get_cipher

# Seuil de similarité au-delà duquel deux souvenirs sont considérés « le même fait ».
DUP_THRESHOLD = 0.92


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ContinuousMemory:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()
        self._cipher = get_cipher()

    @staticmethod
    def _ns(scope: str) -> str:
        return f"ltm:{scope or 'global'}"

    def _reveal(self, rec: dict) -> dict:
        return {
            "id": rec["id"],
            "text": self._cipher.decrypt(rec["enc"]),
            "source": rec.get("source", "user"),
            "importance": rec.get("importance", 0.5),
            "tags": rec.get("tags", []),
            "reinforcement": rec.get("reinforcement", 0),
            "status": rec.get("status", "active"),
            "canonical_id": rec.get("canonical_id"),
            "created_at": rec.get("created_at"),
            "updated_at": rec.get("updated_at"),
        }

    # --- Écriture : apprendre -------------------------------------------
    async def remember(
        self, scope: str, text: str, *, source: str = "user",
        importance: float = 0.5, tags: list[str] | None = None,
    ) -> dict:
        """Enregistre un fait. Si un fait quasi identique existe déjà, le RENFORCE."""
        ns = self._ns(scope)
        vector = (await self._emb.embed([text])).vectors[0]

        # Détection de doublon → renforcement (pas de nouvelle ligne).
        for hit in self._vec.search(ns, vector, 3):
            if hit["score"] >= DUP_THRESHOLD:
                existing = self._store.get(ns, hit["id"])
                if existing and existing.get("status") != "superseded":
                    return self._reinforce_record(ns, existing, importance, tags, source)

        mid = uuid.uuid4().hex
        rec = {
            "id": mid,
            "enc": self._cipher.encrypt(text),
            "source": source,
            "importance": max(0.0, min(1.0, importance)),
            "tags": tags or [],
            "reinforcement": 0,
            "status": "active",
            "canonical_id": None,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._store.put(ns, mid, rec)
        self._vec.upsert(ns, mid, vector, {"mid": mid})
        out = self._reveal(rec)
        out["action"] = "created"
        return out

    def _reinforce_record(self, ns: str, rec: dict, importance: float,
                          tags: list[str] | None, source: str) -> dict:
        rec["reinforcement"] = rec.get("reinforcement", 0) + 1
        rec["importance"] = max(rec.get("importance", 0.5), importance)
        rec["updated_at"] = _now()
        if tags:
            rec["tags"] = sorted(set(rec.get("tags", [])) | set(tags))
        if source and source not in ("user",):
            rec.setdefault("sources", [])
            if source not in rec["sources"]:
                rec["sources"].append(source)
        self._store.put(ns, rec["id"], rec)
        out = self._reveal(rec)
        out["action"] = "reinforced"
        return out

    async def observe(self, scope: str, event: str, *, kind: str = "observation",
                      importance: float = 0.3) -> dict:
        """Ingestion continue d'une interaction / d'un événement (apprentissage passif)."""
        return await self.remember(scope, event, source=kind, importance=importance,
                                   tags=[kind])

    def reinforce(self, scope: str, mid: str) -> bool:
        """Renforce explicitement un souvenir (il s'est révélé utile / confirmé)."""
        ns = self._ns(scope)
        rec = self._store.get(ns, mid)
        if not rec:
            return False
        rec["reinforcement"] = rec.get("reinforcement", 0) + 1
        rec["updated_at"] = _now()
        self._store.put(ns, mid, rec)
        return True

    # --- Lecture : se souvenir ------------------------------------------
    async def recall(self, scope: str, query: str, k: int = 5,
                     include_archived: bool = False) -> list[dict]:
        ns = self._ns(scope)
        qvec = (await self._emb.embed([query])).vectors[0]
        out: list[dict] = []
        for hit in self._vec.search(ns, qvec, max(k * 3, k)):
            rec = self._store.get(ns, hit["id"])
            if not rec:
                continue
            status = rec.get("status", "active")
            if status == "superseded":
                continue
            if status == "archived" and not include_archived:
                continue
            item = self._reveal(rec)
            sim = hit["score"]
            reinforce_boost = 1.0 + math.log1p(rec.get("reinforcement", 0))
            importance_w = 0.5 + rec.get("importance", 0.5)
            item["similarity"] = round(sim, 4)
            item["score"] = round(sim * reinforce_boost * importance_w, 4)
            out.append(item)
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:k]

    def timeline(self, scope: str, include_archived: bool = True) -> list[dict]:
        recs = [self._reveal(r) for r in self._store.list(self._ns(scope))]
        if not include_archived:
            recs = [r for r in recs if r["status"] == "active"]
        recs.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return recs

    # --- Consolidation (non destructive) --------------------------------
    async def consolidate(self, scope: str) -> dict:
        """Lie les quasi-doublons à un canonique (le plus renforcé) et les marque
        `superseded`. Ne supprime RIEN : tout reste rappelable via include_archived.
        """
        ns = self._ns(scope)
        active = [r for r in self._store.list(ns) if r.get("status") == "active"]
        linked = 0
        seen: set[str] = set()
        for rec in active:
            if rec["id"] in seen:
                continue
            vector = (await self._emb.embed([self._cipher.decrypt(rec["enc"])])).vectors[0]
            cluster = []
            for hit in self._vec.search(ns, vector, 10):
                if hit["id"] == rec["id"] or hit["score"] < DUP_THRESHOLD:
                    continue
                other = self._store.get(ns, hit["id"])
                if other and other.get("status") == "active":
                    cluster.append(other)
            if not cluster:
                continue
            group = [rec, *cluster]
            canonical = max(group, key=lambda r: (r.get("reinforcement", 0), r.get("importance", 0)))
            for r in group:
                seen.add(r["id"])
                if r["id"] == canonical["id"]:
                    continue
                r["status"] = "superseded"
                r["canonical_id"] = canonical["id"]
                r["updated_at"] = _now()
                self._store.put(ns, r["id"], r)
                linked += 1
            # le canonique hérite du renforcement cumulé du groupe
            canonical["reinforcement"] = sum(r.get("reinforcement", 0) for r in group) + len(cluster)
            canonical["updated_at"] = _now()
            self._store.put(ns, canonical["id"], canonical)
        return {"scope": scope, "active_scanned": len(active), "linked_superseded": linked}

    # --- Oubli SOFT (tombstone) : jamais de suppression dure ------------
    def archive(self, scope: str, mid: str) -> bool:
        ns = self._ns(scope)
        rec = self._store.get(ns, mid)
        if not rec:
            return False
        rec["status"] = "archived"
        rec["updated_at"] = _now()
        self._store.put(ns, mid, rec)  # conservé : rappelable via include_archived
        return True

    def stats(self, scope: str) -> dict:
        recs = self._store.list(self._ns(scope))
        by_status: dict[str, int] = {}
        by_source: dict[str, int] = {}
        total_reinf = 0
        for r in recs:
            by_status[r.get("status", "active")] = by_status.get(r.get("status", "active"), 0) + 1
            by_source[r.get("source", "user")] = by_source.get(r.get("source", "user"), 0) + 1
            total_reinf += r.get("reinforcement", 0)
        return {
            "scope": scope,
            "total": len(recs),
            "by_status": by_status,
            "by_source": by_source,
            "total_reinforcement": total_reinf,
            "never_forgets": True,
        }


def get_continuous_memory() -> ContinuousMemory:
    return ContinuousMemory()
