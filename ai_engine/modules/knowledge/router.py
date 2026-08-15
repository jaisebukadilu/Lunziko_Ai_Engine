"""Routeur knowledge — /v1/knowledge/{add,search,relations}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.knowledge.engine import ItemType, get_knowledge_engine

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])


class AddRequest(BaseModel):
    org: str = Field(min_length=1)
    type: ItemType
    title: str = Field(min_length=1)
    content: str = Field(default="")
    tags: list[str] = Field(default_factory=list)


class SearchRequest(BaseModel):
    org: str = Field(min_length=1)
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


@router.post("/add")
async def add(req: AddRequest) -> dict:
    try:
        return await get_knowledge_engine().add(req.org, req.type, req.title, req.content, req.tags)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"knowledge.add: {e}")


@router.post("/search")
async def search(req: SearchRequest) -> dict:
    try:
        results = await get_knowledge_engine().search(req.org, req.query, req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"knowledge.search: {e}")
    return {"org": req.org, "results": results}


@router.get("/{org}/{kid}/relations")
def relations(org: str, kid: str) -> dict:
    eng = get_knowledge_engine()
    if eng.get(org, kid) is None:
        raise HTTPException(status_code=404, detail="item introuvable")
    return {"id": kid, "relations": eng.relations(org, kid)}
