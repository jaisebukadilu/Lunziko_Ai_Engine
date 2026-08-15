"""Routeur neural — /v1/neural/{status,backends,route,train}.

Expose le système neuronal : backends disponibles (bibliothèques importées) et routage
d'intention neuronal.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.neural.backends import detect_backends
from ai_engine.modules.neural.router_engine import get_neural_router

router = APIRouter(prefix="/v1/neural", tags=["neural"])


class RouteRequest(BaseModel):
    query: str = Field(min_length=1)


@router.get("/backends")
def backends() -> dict:
    b = detect_backends()
    return {"available": [k for k, v in b.items() if v["available"]], "backends": b}


@router.get("/status")
def status() -> dict:
    rt = get_neural_router()
    b = detect_backends()
    return {
        "available_backends": [k for k, v in b.items() if v["available"]],
        "router_trained": rt.trained,
        "router_backend": rt.backend,
    }


@router.post("/train")
async def train() -> dict:
    try:
        return await get_neural_router().train()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.train: {e}")


@router.post("/route")
async def route(req: RouteRequest) -> dict:
    try:
        return await get_neural_router().route(req.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"neural.route: {e}")
