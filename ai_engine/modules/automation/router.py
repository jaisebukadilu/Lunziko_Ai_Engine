"""Routeur automation — /v1/automation/{flows,flows/{name},run,runs}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai_engine.modules.automation.engine import get_automation_engine

router = APIRouter(prefix="/v1/automation", tags=["automation"])


class Node(BaseModel):
    id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    args: dict = Field(default_factory=dict)


class FlowRequest(BaseModel):
    name: str = Field(min_length=1)
    nodes: list[Node] = Field(min_length=1)
    description: str = ""


class RunRequest(BaseModel):
    input: dict = Field(default_factory=dict)


@router.post("/flows")
def save_flow(req: FlowRequest) -> dict:
    try:
        return get_automation_engine().save_flow(
            req.name, [n.model_dump() for n in req.nodes], req.description)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/flows")
def list_flows() -> dict:
    return {"flows": get_automation_engine().list_flows()}


@router.get("/flows/{name}")
def get_flow(name: str) -> dict:
    rec = get_automation_engine().get_flow(name)
    if rec is None:
        raise HTTPException(status_code=404, detail="flux inconnu")
    return rec


@router.post("/flows/{name}/run")
async def run_flow(name: str, req: RunRequest) -> dict:
    try:
        return await get_automation_engine().run_flow(name, req.input)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs")
def list_runs(flow: str | None = None, limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"runs": get_automation_engine().list_runs(flow, limit)}
