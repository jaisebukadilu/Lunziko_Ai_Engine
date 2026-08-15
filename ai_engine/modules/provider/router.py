"""Routeur provider — monté par le gateway. Expose /v1/chat et /v1/providers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.provider.base import ChatMessage, ChatResult, ProviderError
from ai_engine.modules.provider.manager import get_provider_manager

router = APIRouter(prefix="/v1", tags=["provider"])


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1)
    provider: str | None = None
    system: str | None = None
    model: str | None = None
    max_tokens: int = Field(default=4096, ge=1, le=128000)


@router.get("/providers")
def list_providers() -> dict:
    mgr = get_provider_manager()
    return {"available": mgr.list_available()}


@router.post("/chat", response_model=ChatResult)
async def chat(req: ChatRequest) -> ChatResult:
    mgr = get_provider_manager()
    try:
        return await mgr.chat(
            req.messages,
            provider=req.provider,
            system=req.system,
            model=req.model,
            max_tokens=req.max_tokens,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
