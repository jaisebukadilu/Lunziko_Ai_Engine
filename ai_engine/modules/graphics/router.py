"""Routeur graphics — /v1/graphics/{status,ping,brains,call}.

Client REST du Lunziko Graphics Engine (dépôt séparé). `call` proxie n'importe quel endpoint
REST du moteur (GET/POST). Ex : POST /v1/graphics/call {method:"GET", path:"/agents"}.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.graphics.client import (
    GraphicsEngineClient, graphics_brain_availability, graphics_status,
)

router = APIRouter(prefix="/v1/graphics", tags=["graphics"])


class CallRequest(BaseModel):
    method: str = "GET"
    path: str = Field(min_length=1)          # ex "/agents", "/image/process"
    body: dict = Field(default_factory=dict)


@router.get("/status")
def status() -> dict:
    return graphics_status()


@router.get("/ping")
def ping() -> dict:
    return GraphicsEngineClient().ping()


@router.get("/brains")
def brains() -> dict:
    return {"availability": graphics_brain_availability()}


@router.post("/call")
async def call(req: CallRequest) -> dict:
    try:
        return {"result": await GraphicsEngineClient().call(req.method, req.path, req.body)}
    except RuntimeError as e:
        detail = str(e)
        raise HTTPException(status_code=503 if "non branché" in detail else 502, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"graphics.call: {e}")
