"""Routeur mémoire long-terme (apprentissage continu) — /v1/learning.

Aucune route de suppression dure : la garantie « n'oublie jamais » est structurelle.
`archive` est le seul « oubli », et il conserve la donnée (tombstone rappelable).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.learning.engine import get_continuous_memory

router = APIRouter(prefix="/v1/learning", tags=["learning"])


class RememberRequest(BaseModel):
    scope: str = Field(default="global", description="user_id ou 'global'")
    text: str = Field(min_length=1)
    source: str = "user"
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)


class ObserveRequest(BaseModel):
    scope: str = "global"
    event: str = Field(min_length=1)
    kind: str = "observation"
    importance: float = Field(default=0.3, ge=0.0, le=1.0)


class RecallRequest(BaseModel):
    scope: str = "global"
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)
    include_archived: bool = False


@router.post("/remember")
async def remember(req: RememberRequest) -> dict:
    return await get_continuous_memory().remember(
        req.scope, req.text, source=req.source, importance=req.importance, tags=req.tags)


@router.post("/observe")
async def observe(req: ObserveRequest) -> dict:
    return await get_continuous_memory().observe(
        req.scope, req.event, kind=req.kind, importance=req.importance)


@router.post("/recall")
async def recall(req: RecallRequest) -> list[dict]:
    return await get_continuous_memory().recall(
        req.scope, req.query, k=req.k, include_archived=req.include_archived)


@router.post("/reinforce/{scope}/{mid}")
def reinforce(scope: str, mid: str) -> dict:
    if not get_continuous_memory().reinforce(scope, mid):
        raise HTTPException(status_code=404, detail="souvenir introuvable")
    return {"scope": scope, "id": mid, "status": "reinforced"}


@router.post("/consolidate/{scope}")
async def consolidate(scope: str) -> dict:
    return await get_continuous_memory().consolidate(scope)


@router.get("/timeline/{scope}")
def timeline(scope: str, include_archived: bool = True) -> list[dict]:
    return get_continuous_memory().timeline(scope, include_archived=include_archived)


@router.post("/archive/{scope}/{mid}")
def archive(scope: str, mid: str) -> dict:
    if not get_continuous_memory().archive(scope, mid):
        raise HTTPException(status_code=404, detail="souvenir introuvable")
    return {"scope": scope, "id": mid, "status": "archived",
            "note": "conservé (tombstone) — rappelable via include_archived, jamais supprimé"}


@router.get("/stats/{scope}")
def stats(scope: str) -> dict:
    return get_continuous_memory().stats(scope)
