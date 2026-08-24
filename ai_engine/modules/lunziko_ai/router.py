"""Routeur Lunziko AI — /v1/lunziko-ai : assistant intégré 5 piliers, appelable par toute app."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.lunziko_ai.engine import get_lunziko_assistant

router = APIRouter(prefix="/v1/lunziko-ai", tags=["lunziko-ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    scope: str = "global"
    provider: str | None = Field(default=None, description="ex 'ollama-mistral' pour le 2e modèle")
    use_web: bool | None = Field(default=None, description="null = auto-détection")
    learn: bool = True


class RememberRequest(BaseModel):
    scope: str = "global"
    fact: str = Field(min_length=1)
    importance: float = Field(default=0.8, ge=0.0, le=1.0)


@router.post("/chat")
async def chat(req: ChatRequest) -> dict:
    try:
        return await get_lunziko_assistant().chat(
            req.message, scope=req.scope, provider=req.provider,
            use_web=req.use_web, learn=req.learn)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"lunziko-ai: {e}")


@router.post("/remember")
async def remember(req: RememberRequest) -> dict:
    return await get_lunziko_assistant().remember(req.scope, req.fact, req.importance)


@router.get("/status")
def status() -> dict:
    from ai_engine.config import get_settings
    from ai_engine.modules.provider.manager import get_provider_manager
    s = get_settings()
    return {
        "pillars": {
            "big_model": s.ae_local_model or s.ae_default_provider,
            "knowledge": "ecosystem (registre)",
            "persistent_memory": "learning (n'oublie jamais)",
            "continuous_learning": True,
            "web_search": s.ae_search_backend,
        },
        "second_model": [p for p in get_provider_manager().list_available() if p.startswith("ollama-")],
        "note": "POST /v1/lunziko-ai/chat {message, scope, provider?, use_web?}",
    }
