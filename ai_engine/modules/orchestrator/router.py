"""Routeur LAIA — /v1/brains, /v1/engines, /v1/orchestrator, /v1/blackboard, /v1/validate."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.orchestrator.blackboard import get_blackboard
from ai_engine.modules.orchestrator.brains import get_brain_registry
from ai_engine.modules.orchestrator.engine import get_orchestrator
from ai_engine.modules.orchestrator.engines import get_engine, list_engines
from ai_engine.modules.orchestrator.validation import supported_types, validate

router = APIRouter(prefix="/v1", tags=["laia"])


class BrainManifest(BaseModel):
    id: str = Field(min_length=1)
    name: str = ""
    type: str = ""
    capabilities: list[str] = Field(default_factory=list)
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    engines: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    status: str = "active"


class ResolveRequest(BaseModel):
    query: str = Field(min_length=1)
    only_active: bool = False
    k: int = Field(default=3, ge=1, le=16)


class OrchestrateRequest(BaseModel):
    goal: str = Field(min_length=1)
    user_id: str | None = None
    app: str | None = None
    provider: str | None = None


class ValidateRequest(BaseModel):
    type: str = Field(min_length=1)
    content: object


# --- Brains ---
@router.get("/brains")
def brains(status: str | None = None) -> dict:
    items = get_brain_registry().list(status)
    return {"count": len(items), "brains": items}


@router.get("/brains/{bid}")
def brain(bid: str) -> dict:
    rec = get_brain_registry().get(bid)
    if rec is None:
        raise HTTPException(status_code=404, detail="brain inconnu")
    return rec


@router.get("/brains/{bid}/capabilities")
def brain_capabilities(bid: str) -> dict:
    if get_brain_registry().get(bid) is None:
        raise HTTPException(status_code=404, detail="brain inconnu")
    return {"id": bid, "capabilities": get_brain_registry().capabilities(bid)}


@router.post("/brains/register")
def register_brain(req: BrainManifest) -> dict:
    return get_brain_registry().register(req.model_dump())


@router.post("/brains/resolve")
def resolve_brain(req: ResolveRequest) -> dict:
    return {"query": req.query,
            "brains": get_brain_registry().resolve(req.query, only_active=req.only_active, k=req.k)}


# --- Engines ---
@router.get("/engines")
def engines(status: str | None = None) -> dict:
    items = list_engines(status)
    return {"count": len(items), "engines": items}


@router.get("/engines/{eid}")
def engine(eid: str) -> dict:
    rec = get_engine(eid)
    if rec is None:
        raise HTTPException(status_code=404, detail="engine inconnu")
    return rec


# --- Orchestrator ---
@router.post("/orchestrator/plan")
async def orchestrate_plan(req: OrchestrateRequest) -> dict:
    return await get_orchestrator().plan(req.goal, user_id=req.user_id, app=req.app)


@router.post("/orchestrator/run")
async def orchestrate_run(req: OrchestrateRequest) -> dict:
    return await get_orchestrator().run(req.goal, user_id=req.user_id, app=req.app, provider=req.provider)


# --- Blackboard ---
@router.get("/blackboard/tasks/{tid}")
def blackboard_task(tid: str) -> dict:
    rec = get_blackboard().get(tid)
    if rec is None:
        raise HTTPException(status_code=404, detail="tâche inconnue")
    return rec


@router.get("/blackboard/tasks")
def blackboard_tasks() -> dict:
    return {"tasks": get_blackboard().list()}


# --- Validation ---
@router.post("/validate")
def validate_artifact(req: ValidateRequest) -> dict:
    return validate(req.type, req.content)


@router.get("/validate/types")
def validate_types() -> dict:
    return {"types": supported_types()}
