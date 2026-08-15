"""Routeur agents — /v1/agent/{run,capabilities}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.agents.engine import CAPABILITIES, get_agent_engine
from ai_engine.modules.provider.base import ProviderError

router = APIRouter(prefix="/v1/agent", tags=["agents"])


class RunRequest(BaseModel):
    query: str = Field(min_length=1)
    agent: str = "auto"
    user_id: str | None = None
    org: str | None = None
    provider: str | None = None
    save_memory: bool = False
    use_ecosystem: bool = True
    use_activity: bool = True
    use_neural_router: bool = True
    max_tokens: int = Field(default=1024, ge=1, le=128000)


@router.get("/capabilities")
def capabilities() -> dict:
    return {"capabilities": ["auto", *CAPABILITIES.keys(), "general"]}


@router.post("/run")
async def run(req: RunRequest) -> dict:
    try:
        return await get_agent_engine().run(
            req.query,
            agent=req.agent,
            user_id=req.user_id,
            org=req.org,
            provider=req.provider,
            save_memory=req.save_memory,
            use_ecosystem=req.use_ecosystem,
            use_activity=req.use_activity,
            use_neural_router=req.use_neural_router,
            max_tokens=req.max_tokens,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
