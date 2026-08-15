"""EcosystemEngine — ingère le registre maître Lunziko dans l'AI Engine (runtime).

Au démarrage (et à la demande via /v1/ecosystem/sync), lit le fichier racine
REGISTRE_ECOSYSTEME_LUNZIKO.md, le parse (parser.py) et le projette :
  - StoragePort  ns=``ecosystem``      : une entrée par application (id = slug, idempotent) ;
  - VectorPort   ns=``ecosystem``      : vecteur par application (recherche sémantique) ;
  - StoragePort  ns=``ecosystem_meta`` : métadonnées de sync (version, source, horodatage).

Fonctionne hors-ligne (repli embeddings hash). La sync est idempotente : les slugs
disparus du registre sont retirés du store et de l'index.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ai_engine.config import get_settings
from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.ecosystem.parser import parse_registry
from ai_engine.modules.embeddings.manager import get_embedding_manager

NS_APP = "ecosystem"
NS_META = "ecosystem_meta"
META_KEY = "sync"


def resolve_registry_path() -> Path | None:
    """Chemin du registre : override config, sinon découverte relative au dépôt.

    Le code vit dans ``…/Lunziko/Lunziko AI Engine/lunziko-ai-engine/ai_engine/modules/ecosystem`` ;
    le registre est à la racine ``…/Lunziko/REGISTRE_ECOSYSTEME_LUNZIKO.md``.
    """
    s = get_settings()
    if s.ae_registry_path:
        p = Path(s.ae_registry_path).expanduser()
        return p if p.is_file() else None

    name = "REGISTRE_ECOSYSTEME_LUNZIKO.md"
    here = Path(__file__).resolve()
    candidates = [parent / name for parent in here.parents]
    candidates.append(Path.cwd() / name)
    for c in candidates:
        if c.is_file():
            return c
    return None


class EcosystemEngine:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()

    # --- Lecture -----------------------------------------------------------
    def list_apps(self, *, aggregators_only: bool = False) -> list[dict]:
        apps = [a for a in self._store.list(NS_APP)]
        if aggregators_only:
            apps = [a for a in apps if a.get("is_aggregator")]
        return sorted(apps, key=lambda a: (not a.get("is_aggregator"), a.get("slug", "")))

    def get_app(self, slug: str) -> dict | None:
        return self._store.get(NS_APP, slug)

    def meta(self) -> dict | None:
        return self._store.get(NS_META, META_KEY)

    async def search(self, query: str, k: int = 5) -> list[dict]:
        qvec = (await self._emb.embed([query])).vectors[0]
        out: list[dict] = []
        for hit in self._vec.search(NS_APP, qvec, k):
            rec = self._store.get(NS_APP, hit["id"])
            if rec:
                out.append({**rec, "score": round(hit["score"], 4)})
        return out

    # --- Écriture ----------------------------------------------------------
    async def sync(self, *, path: str | None = None) -> dict:
        src = Path(path).expanduser() if path else resolve_registry_path()
        if src is None or not src.is_file():
            return {"synced": False, "reason": "registre introuvable",
                    "hint": "définir AE_REGISTRY_PATH ou placer le fichier à la racine Lunziko"}

        markdown = src.read_text(encoding="utf-8")
        parsed = parse_registry(markdown)
        apps = parsed["apps"]
        new_slugs = {a["slug"] for a in apps}

        # Retrait des slugs disparus (idempotence).
        removed = []
        for rec in self._store.list(NS_APP):
            slug = rec.get("slug")
            if slug and slug not in new_slugs:
                self._store.delete(NS_APP, slug)
                self._vec.delete(NS_APP, slug)
                removed.append(slug)

        # Upsert de chaque application.
        from ai_engine.modules.ecosystem.parser import AppEntry

        now = datetime.now(timezone.utc).isoformat()
        for a in apps:
            entry = AppEntry(**a)
            rec = {**a, "updated_at": now}
            self._store.put(NS_APP, entry.slug, rec)
            vector = (await self._emb.embed([entry.searchable_text()])).vectors[0]
            self._vec.upsert(NS_APP, entry.slug, vector, {"slug": entry.slug, "name": entry.name})

        meta = {
            "id": META_KEY,
            "version": parsed["version"],
            "source": str(src),
            "count": len(apps),
            "embedder": self._emb.active_name,
            "removed": removed,
            "synced_at": now,
        }
        self._store.put(NS_META, META_KEY, meta)
        return {"synced": True, **meta, "slugs": sorted(new_slugs)}


def get_ecosystem_engine() -> EcosystemEngine:
    return EcosystemEngine()
