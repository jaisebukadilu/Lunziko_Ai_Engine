"""Routeur feedback — /v1/feedback (record), /v1/feedback/{stats,corrections}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai_engine.modules.feedback.engine import get_feedback_engine

router = APIRouter(prefix="/v1/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
    target_id: str = ""
    user_id: str | None = None
    query: str = ""
    answer: str = ""
    correction: str = ""
    app: str | None = None


@router.post("")
def record(req: FeedbackRequest) -> dict:
    try:
        return get_feedback_engine().record(
            rating=req.rating, target_id=req.target_id, user_id=req.user_id,
            query=req.query, answer=req.answer, correction=req.correction, app=req.app)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/stats")
def stats(app: str | None = None) -> dict:
    return get_feedback_engine().stats(app=app)


@router.get("/corrections")
def corrections(app: str | None = None, limit: int = Query(default=10, ge=1, le=50)) -> dict:
    return {"corrections": get_feedback_engine().corrections(app=app, limit=limit)}
