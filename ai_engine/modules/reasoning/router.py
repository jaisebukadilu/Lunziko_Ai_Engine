"""Routeur raisonnement avancé — /v1/reasoning."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.reasoning.engine import get_reasoning_engine
from ai_engine.modules.reasoning.strategies import all_strategies, get_strategy

router = APIRouter(prefix="/v1/reasoning", tags=["reasoning"])


class ReasonRequest(BaseModel):
    question: str = Field(min_length=1)
    strategy: str = "auto"
    n: int = Field(default=5, ge=1, le=15)          # self-consistency
    breadth: int = Field(default=3, ge=2, le=8)     # tree-of-thoughts


@router.get("/strategies")
def strategies() -> list[dict]:
    return all_strategies()


@router.get("/strategies/{sid}")
def strategy(sid: str) -> dict:
    s = get_strategy(sid)
    if s is None:
        raise HTTPException(status_code=404, detail=f"stratégie inconnue: {sid}")
    return s


@router.post("/reason")
async def reason(req: ReasonRequest) -> dict:
    try:
        return await get_reasoning_engine().reason(
            req.question, strategy=req.strategy, n=req.n, breadth=req.breadth)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"reasoning: {e}")
