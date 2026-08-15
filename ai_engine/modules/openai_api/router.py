"""Routeur compatible OpenAI. Auth Bearer/X-API-Key gérée au montage (gateway)."""

from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.provider.base import ChatMessage, ProviderError
from ai_engine.modules.provider.manager import get_provider_manager

router = APIRouter(prefix="/v1", tags=["openai-compat"])

_PROVIDERS = {"claude", "chatgpt", "gemini", "mistral", "deepseek", "local"}


class OAIMessage(BaseModel):
    role: str
    content: str = ""


class ChatCompletionRequest(BaseModel):
    model: str = "lunziko-auto"
    messages: list[OAIMessage] = Field(min_length=1)
    max_tokens: int = Field(default=1024, ge=1, le=128000)
    stream: bool = False


class EmbeddingsRequest(BaseModel):
    model: str = "lunziko-embed"
    input: str | list[str]


def _resolve_model(model: str) -> tuple[str | None, str | None]:
    """(provider, model_override) à partir du champ OpenAI `model`."""
    if not model or model in ("lunziko-auto", "auto"):
        return None, None
    if model in _PROVIDERS:
        return model, None
    return None, model  # id de modèle -> cascade par défaut avec ce modèle


def _split(messages: list[OAIMessage]) -> tuple[str | None, list[ChatMessage]]:
    system_parts = [m.content for m in messages if m.role == "system"]
    convo = [
        ChatMessage(role="assistant" if m.role == "assistant" else "user", content=m.content)
        for m in messages
        if m.role in ("user", "assistant")
    ]
    if not convo:  # au moins un tour utilisateur
        convo = [ChatMessage(role="user", content="")]
    return ("\n".join(system_parts) or None), convo


@router.get("/models")
def list_models() -> dict:
    avail = get_provider_manager().list_available()
    ids = ["lunziko-auto", *avail]
    created = int(time.time())
    return {
        "object": "list",
        "data": [{"id": i, "object": "model", "created": created, "owned_by": "lunziko"} for i in ids],
    }


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    provider, model_override = _resolve_model(req.model)
    system, convo = _split(req.messages)
    try:
        result = await get_provider_manager().chat(
            convo, provider=provider, system=system, model=model_override, max_tokens=req.max_tokens
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    cid = "chatcmpl-" + uuid.uuid4().hex
    created = int(time.time())

    if not req.stream:
        return {
            "id": cid,
            "object": "chat.completion",
            "created": created,
            "model": result.model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result.content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": result.input_tokens,
                "completion_tokens": result.output_tokens,
                "total_tokens": result.input_tokens + result.output_tokens,
            },
        }

    # Pseudo-streaming SSE (réponse calculée puis découpée) — compatible clients OpenAI.
    # Le vrai streaming token-par-token viendra avec le chatStream provider (suivi).
    def _chunk(delta: dict, finish=None) -> str:
        payload = {
            "id": cid,
            "object": "chat.completion.chunk",
            "created": created,
            "model": result.model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def gen():
        yield _chunk({"role": "assistant"})
        text = result.content
        for i in range(0, len(text), 48):
            yield _chunk({"content": text[i:i + 48]})
        yield _chunk({}, finish="stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/embeddings")
async def embeddings(req: EmbeddingsRequest) -> dict:
    texts = [req.input] if isinstance(req.input, str) else req.input
    try:
        res = await get_embedding_manager().embed(texts)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"embeddings: {e}")
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(res.vectors)
        ],
        "model": res.model,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
