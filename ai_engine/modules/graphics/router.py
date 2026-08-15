"""Routeur graphics — /v1/graphics/{status,ping,brains,call}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.graphics.client import (
    GraphicsEngineClient, graphics_brain_availability, graphics_status,
)

router = APIRouter(prefix="/v1/graphics", tags=["graphics"])


class CallRequest(BaseModel):
    method: str = Field(min_length=1)
    params: dict = Field(default_factory=dict)


@router.get("/status")
def status() -> dict:
    return graphics_status()


@router.get("/ping")
def ping() -> dict:
    return GraphicsEngineClient().ping()


@router.get("/brains")
def brains() -> dict:
    """Statut effectif des Brains dépendant du Graphics Engine (active si branché)."""
    return {"availability": graphics_brain_availability()}


@router.post("/call")
async def call(req: CallRequest) -> dict:
    try:
        return {"result": await GraphicsEngineClient().call(req.method, req.params)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"graphics.call: {e}")
