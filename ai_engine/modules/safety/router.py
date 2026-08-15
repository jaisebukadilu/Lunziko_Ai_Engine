"""Routeur safety — /v1/safety/{check,redact}."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_engine.modules.safety.engine import check, redact

router = APIRouter(prefix="/v1/safety", tags=["safety"])


class CheckRequest(BaseModel):
    text: str = Field(min_length=1)
    direction: str = "input"  # input | output


class RedactRequest(BaseModel):
    text: str = Field(min_length=1)


@router.post("/check")
def safety_check(req: CheckRequest) -> dict:
    return check(req.text, direction=req.direction)


@router.post("/redact")
def safety_redact(req: RedactRequest) -> dict:
    return redact(req.text)
