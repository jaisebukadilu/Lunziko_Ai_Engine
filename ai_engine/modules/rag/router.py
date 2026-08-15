"""Routeur RAG — /v1/rag/{index,search,query}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.provider.base import ProviderError
from ai_engine.modules.rag.service import get_rag_service

router = APIRouter(prefix="/v1/rag", tags=["rag"])


class IndexRequest(BaseModel):
    namespace: str = Field(min_length=1)
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    meta: dict | None = None


class SearchRequest(BaseModel):
    namespace: str = Field(min_length=1)
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


class QueryRequest(SearchRequest):
    provider: str | None = None
    system: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=128000)


@router.post("/index")
async def index(req: IndexRequest) -> dict:
    try:
        n = await get_rag_service().index(req.namespace, req.id, req.text, req.meta)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"index: {e}")
    return {"namespace": req.namespace, "id": req.id, "chunks_indexed": n}


@router.post("/search")
async def search(req: SearchRequest) -> dict:
    try:
        results = await get_rag_service().search(req.namespace, req.query, req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"search: {e}")
    return {"namespace": req.namespace, "results": results}


@router.post("/query")
async def query(req: QueryRequest) -> dict:
    try:
        return await get_rag_service().query(
            req.namespace, req.query, req.k,
            provider=req.provider, system=req.system, max_tokens=req.max_tokens,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"query: {e}")
