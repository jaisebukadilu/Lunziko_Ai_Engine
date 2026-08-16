"""Routeur search — /v1/search + /v1/search/status."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.search.engine import get_search_engine

router = APIRouter(prefix="/v1/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=25)
    backend: str | None = None


@router.get("/status")
def status() -> dict:
    return get_search_engine().status()


@router.post("")
async def search(req: SearchRequest) -> dict:
    try:
        return await get_search_engine().search(req.query, k=req.k, backend=req.backend)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"search: {e}")
