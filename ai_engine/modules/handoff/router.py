"""Routeur handoff — /v1/handoff/{redirect,open-with,transfer,file-types}."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_engine.modules.handoff.engine import get_handoff_engine
from ai_engine.modules.handoff.filetypes import known_extensions

router = APIRouter(prefix="/v1/handoff", tags=["handoff"])


class RedirectRequest(BaseModel):
    from_app: str = Field(min_length=1)
    task: str = Field(min_length=1)
    user_id: str | None = None


class OpenWithRequest(BaseModel):
    from_app: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    hint: str = ""
    user_id: str | None = None


class TransferRequest(BaseModel):
    from_app: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    to_app: str | None = None
    mode: str = "copy"
    is_folder: bool = False
    hint: str = ""
    user_id: str | None = None


@router.get("/file-types")
def file_types() -> dict:
    return {"extensions": known_extensions()}


@router.post("/redirect")
async def redirect(req: RedirectRequest) -> dict:
    return await get_handoff_engine().redirect(req.from_app, req.task, user_id=req.user_id)


@router.post("/open-with")
async def open_with(req: OpenWithRequest) -> dict:
    return await get_handoff_engine().open_with(
        req.from_app, req.filename, hint=req.hint, user_id=req.user_id
    )


@router.post("/transfer")
async def transfer(req: TransferRequest) -> dict:
    return await get_handoff_engine().transfer(
        req.from_app, req.resource, to_app=req.to_app, mode=req.mode,
        is_folder=req.is_folder, hint=req.hint, user_id=req.user_id
    )
