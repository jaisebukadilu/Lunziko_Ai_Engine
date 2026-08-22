"""Routeur autonomie & résilience — /v1/autonomy."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_engine.modules.autonomy.engine import get_resilient_agent
from ai_engine.modules.autonomy.persona import RESILIENT_PERSONA

router = APIRouter(prefix="/v1/autonomy", tags=["autonomy"])


class SolveRequest(BaseModel):
    goal: str = Field(min_length=1)
    scope: str = "global"
    max_iterations: int = Field(default=6, ge=1, le=20)


@router.post("/solve")
async def solve(req: SolveRequest) -> dict:
    return await get_resilient_agent().solve(
        req.goal, scope=req.scope, max_iterations=req.max_iterations)


@router.get("/persona")
def persona() -> dict:
    return {"persona": RESILIENT_PERSONA, "never_gives_up": True,
            "consults_memory_before_acting": True, "learns_from_errors": True}
