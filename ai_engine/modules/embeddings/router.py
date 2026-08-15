"""Routeur embeddings — /v1/embed."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.embeddings.base import EmbedResult
from ai_engine.modules.embeddings.manager import get_embedding_manager

router = APIRouter(prefix="/v1", tags=["embeddings"])


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


@router.post("/embed", response_model=EmbedResult)
async def embed(req: EmbedRequest) -> EmbedResult:
    try:
        return await get_embedding_manager().embed(req.texts)
    except Exception as e:  # provider indisponible malgré le repli -> 502
        raise HTTPException(status_code=502, detail=f"embed: {e}")
