"""Routeur actions — /v1/actions/{register,(list),{app}/{action},invoke}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.actions.engine import get_action_registry

router = APIRouter(prefix="/v1/actions", tags=["actions"])


class RegisterRequest(BaseModel):
    app: str = Field(min_length=1)
    action: str = Field(min_length=1)
    description: str = ""
    parameters: dict = Field(default_factory=dict)
    requires_confirmation: bool = False
    executor: str = "host"


class InvokeRequest(BaseModel):
    app: str = Field(min_length=1)
    action: str = Field(min_length=1)
    arguments: dict = Field(default_factory=dict)
    user_id: str | None = None


@router.post("/register")
def register(req: RegisterRequest) -> dict:
    return get_action_registry().register(
        req.app, req.action, req.description, req.parameters,
        req.requires_confirmation, req.executor)


@router.get("")
def list_actions(app: str | None = None) -> dict:
    items = get_action_registry().list(app)
    return {"count": len(items), "actions": items}


@router.get("/{app}/{action}")
def get_action(app: str, action: str) -> dict:
    rec = get_action_registry().get(app, action)
    if rec is None:
        raise HTTPException(status_code=404, detail="action inconnue")
    return rec


@router.post("/invoke")
def invoke(req: InvokeRequest) -> dict:
    try:
        return get_action_registry().invoke(req.app, req.action, req.arguments, user_id=req.user_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
