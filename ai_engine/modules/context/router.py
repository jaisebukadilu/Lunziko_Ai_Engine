"""Routeur context — /v1/appstate/*, /v1/profile/*, /v1/context/assemble."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ai_engine.modules.context.appstate import get_appstate_store
from ai_engine.modules.context.assembler import get_context_assembler
from ai_engine.modules.context.profile import get_profile_store

router = APIRouter(prefix="/v1", tags=["context"])


class AppStateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    app: str = Field(min_length=1)
    screen: str = ""
    form_draft: dict = Field(default_factory=dict)
    last_error: str = ""
    ttl: int = Field(default=900, ge=1, le=86400)


class ProfileRequest(BaseModel):
    user_id: str = Field(min_length=1)
    role: str | None = None
    language: str | None = None
    preferences: dict | None = None


class AssembleRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query: str = ""
    app: str | None = None
    timezone_name: str | None = None
    location: str | None = None


@router.put("/appstate")
def put_appstate(req: AppStateRequest) -> dict:
    return get_appstate_store().put(
        req.user_id, req.app, screen=req.screen, form_draft=req.form_draft,
        last_error=req.last_error, ttl=req.ttl)


@router.get("/appstate")
def get_appstate(user_id: str = Query(min_length=1), app: str | None = None) -> dict:
    return {"user_id": user_id, "state": get_appstate_store().get(user_id, app)}


@router.get("/profile/{user_id}")
def get_profile(user_id: str) -> dict:
    return get_profile_store().get(user_id)


@router.put("/profile")
def set_profile(req: ProfileRequest) -> dict:
    return get_profile_store().set(req.user_id, role=req.role, language=req.language,
                                   preferences=req.preferences)


@router.get("/profile/{user_id}/habits")
def habits(user_id: str) -> dict:
    return get_profile_store().habits(user_id)


@router.post("/context/assemble")
async def assemble(req: AssembleRequest) -> dict:
    return await get_context_assembler().assemble(
        req.user_id, query=req.query, app=req.app,
        timezone_name=req.timezone_name, location=req.location)
