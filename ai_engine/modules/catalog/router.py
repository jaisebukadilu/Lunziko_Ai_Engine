"""Routeur catalog — /v1/catalog/{register,schemas,schemas/{id},resolve}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.catalog.engine import get_catalog_engine

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])


class RegisterRequest(BaseModel):
    app: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    fields: dict = Field(default_factory=dict)
    description: str = ""


class ResolveRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=3, ge=1, le=20)


@router.post("/register")
async def register(req: RegisterRequest) -> dict:
    try:
        return await get_catalog_engine().register(req.app, req.dataset, req.fields, req.description)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"catalog.register: {e}")


@router.get("/schemas")
def schemas(app: str | None = None) -> dict:
    items = get_catalog_engine().list(app)
    return {"count": len(items), "schemas": items}


@router.get("/schemas/{sid}")
def get_schema(sid: str) -> dict:
    rec = get_catalog_engine().get(sid)
    if rec is None:
        raise HTTPException(status_code=404, detail="schéma inconnu")
    return rec


@router.post("/resolve")
async def resolve(req: ResolveRequest) -> dict:
    try:
        return {"query": req.query, "matches": await get_catalog_engine().resolve(req.query, req.k)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"catalog.resolve: {e}")
