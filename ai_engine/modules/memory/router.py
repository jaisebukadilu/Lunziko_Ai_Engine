"""Routeur mémoire — /v1/memory/{save,list,recall} + delete."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.memory.engine import Category, get_memory_engine

router = APIRouter(prefix="/v1/memory", tags=["memory"])


class SaveRequest(BaseModel):
    user_id: str = Field(min_length=1)
    category: Category = "general"
    key: str = Field(min_length=1)
    value: str = Field(min_length=1)


class RecallRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


@router.post("/save")
async def save(req: SaveRequest) -> dict:
    try:
        mid = await get_memory_engine().save(req.user_id, req.category, req.key, req.value)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"memory.save: {e}")
    return {"id": mid}


@router.get("/list")
def list_memory(user_id: str) -> dict:
    return {"user_id": user_id, "items": get_memory_engine().list(user_id)}


@router.post("/recall")
async def recall(req: RecallRequest) -> dict:
    try:
        items = await get_memory_engine().recall(req.user_id, req.query, req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"memory.recall: {e}")
    return {"user_id": req.user_id, "items": items}


@router.delete("/{user_id}/{mid}")
def delete(user_id: str, mid: str) -> dict:
    if not get_memory_engine().delete(user_id, mid):
        raise HTTPException(status_code=404, detail="mémoire introuvable")
    return {"deleted": mid}
