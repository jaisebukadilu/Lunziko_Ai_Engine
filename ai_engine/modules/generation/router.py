"""Routeur génération multimédia — /v1/generate."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.generation.engine import get_generation_engine

router = APIRouter(prefix="/v1/generate", tags=["generation"])


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    backend: str | None = None
    options: dict = Field(default_factory=dict)


@router.get("/status")
def status() -> dict:
    return get_generation_engine().status()


@router.get("/backends")
def backends() -> dict:
    from ai_engine.modules.generation.backends import available_backends
    return available_backends()


@router.get("/models/{kind}")
def models(kind: str) -> list[dict]:
    return get_generation_engine().models_for(kind)


async def _gen(kind: str, req: GenerateRequest) -> dict:
    try:
        return await get_generation_engine().generate(
            kind, req.prompt, backend=req.backend, options=req.options)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/image")
async def image(req: GenerateRequest) -> dict:
    return await _gen("image", req)


@router.post("/video")
async def video(req: GenerateRequest) -> dict:
    return await _gen("video", req)


@router.post("/audio")
async def audio(req: GenerateRequest) -> dict:
    return await _gen("audio", req)


@router.post("/music")
async def music(req: GenerateRequest) -> dict:
    return await _gen("music", req)


@router.post("/3d")
async def three_d(req: GenerateRequest) -> dict:
    return await _gen("3d", req)
