"""Routeur écosystème — /v1/ecosystem/{sync,apps,apps/{slug},search,status}.

Expose la connaissance runtime du registre maître Lunziko : l'AI Engine sait quelles
applications existent, ce qu'elles font, ce qu'elles exposent/consomment.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai_engine.modules.ecosystem.engine import get_ecosystem_engine, resolve_registry_path

router = APIRouter(prefix="/v1/ecosystem", tags=["ecosystem"])


class SyncRequest(BaseModel):
    path: str | None = Field(default=None, description="chemin explicite du registre (sinon découverte)")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


@router.get("/status")
def status() -> dict:
    eng = get_ecosystem_engine()
    src = resolve_registry_path()
    return {
        "registry_found": src is not None,
        "registry_path": str(src) if src else None,
        "last_sync": eng.meta(),
        "apps_indexed": len(eng.list_apps()),
    }


@router.post("/sync")
async def sync(req: SyncRequest | None = None) -> dict:
    path = req.path if req else None
    try:
        return await get_ecosystem_engine().sync(path=path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ecosystem.sync: {e}")


@router.get("/apps")
def apps(aggregators_only: bool = Query(default=False)) -> dict:
    items = get_ecosystem_engine().list_apps(aggregators_only=aggregators_only)
    return {"count": len(items), "apps": items}


@router.get("/apps/{slug}")
def app(slug: str) -> dict:
    rec = get_ecosystem_engine().get_app(slug)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"application inconnue : {slug}")
    return rec


@router.post("/search")
async def search(req: SearchRequest) -> dict:
    try:
        results = await get_ecosystem_engine().search(req.query, req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ecosystem.search: {e}")
    return {"query": req.query, "results": results}
