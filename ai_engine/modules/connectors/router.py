"""Routeur connectors — /v1/connectors/{types,ingest,namespaces,search}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.connectors.engine import CONNECTOR_TYPES, get_connector_engine

router = APIRouter(prefix="/v1/connectors", tags=["connectors"])


class IngestRequest(BaseModel):
    connector: str = Field(min_length=1)
    namespace: str = Field(min_length=1)
    items: list[dict] = Field(min_length=1)


class UnifiedSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    namespaces: list[str] | None = None
    k: int = Field(default=5, ge=1, le=50)


@router.get("/types")
def types() -> dict:
    return {"connectors": CONNECTOR_TYPES}


@router.get("/namespaces")
def namespaces() -> dict:
    return {"namespaces": get_connector_engine().namespaces()}


@router.post("/ingest")
async def ingest(req: IngestRequest) -> dict:
    try:
        return await get_connector_engine().ingest(req.connector, req.namespace, req.items)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"connectors.ingest: {e}")


@router.post("/search")
async def search(req: UnifiedSearchRequest) -> dict:
    try:
        results = await get_connector_engine().unified_search(req.query, namespaces=req.namespaces, k=req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"connectors.search: {e}")
    return {"query": req.query, "results": results}
