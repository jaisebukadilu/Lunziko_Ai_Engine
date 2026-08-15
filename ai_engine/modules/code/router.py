"""Routeur code — /v1/code/{analyze,debug,explain}. Priorité modèles locaux (Ollama)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.code.engine import get_code_engine
from ai_engine.modules.provider.base import ProviderError

router = APIRouter(prefix="/v1/code", tags=["code"])


class AnalyzeRequest(BaseModel):
    code: str = Field(min_length=1)
    question: str | None = None
    provider: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=1500, ge=1, le=128000)


class DebugRequest(BaseModel):
    code: str = Field(min_length=1)
    error: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=1500, ge=1, le=128000)


class ExplainRequest(BaseModel):
    code: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=1500, ge=1, le=128000)


@router.post("/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    try:
        return await get_code_engine().analyze(
            req.code, req.question, provider=req.provider, model=req.model, max_tokens=req.max_tokens
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/debug")
async def debug(req: DebugRequest) -> dict:
    try:
        return await get_code_engine().debug(
            req.code, req.error, provider=req.provider, model=req.model, max_tokens=req.max_tokens
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/explain")
async def explain(req: ExplainRequest) -> dict:
    try:
        return await get_code_engine().explain(
            req.code, provider=req.provider, model=req.model, max_tokens=req.max_tokens
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
