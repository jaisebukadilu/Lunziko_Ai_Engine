"""Routeur workflows — /v1/workflow/{types,run,runs,run/{id}}."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.workflows.engine import get_workflow_engine

router = APIRouter(prefix="/v1/workflow", tags=["workflows"])


class RunRequest(BaseModel):
    type: str = Field(min_length=1)
    inputs: dict = Field(default_factory=dict)


@router.get("/types")
def types() -> dict:
    return {"types": get_workflow_engine().types()}


@router.post("/run")
async def run(req: RunRequest) -> dict:
    eng = get_workflow_engine()
    try:
        return await eng.run(req.type, req.inputs)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs")
def runs() -> dict:
    return {"runs": get_workflow_engine().list_runs()}


@router.get("/run/{run_id}")
def get_run(run_id: str) -> dict:
    rec = get_workflow_engine().get_run(run_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="run introuvable")
    return rec
