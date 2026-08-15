"""Routeur activity — /v1/activity/{log,log-batch,timeline,search,summary} + DELETE.

Journal des actions utilisateur : les applications de la suite y publient ce que fait
l'utilisateur ; l'AI Engine s'en sert comme contexte comportemental pour l'accompagner.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ai_engine.modules.activity.engine import get_activity_engine

router = APIRouter(prefix="/v1/activity", tags=["activity"])


class Event(BaseModel):
    app: str = Field(min_length=1)
    action: str = Field(min_length=1)
    target: str = ""
    status: str = "ok"
    detail: str = ""
    session_id: str | None = None
    meta: dict = Field(default_factory=dict)
    ts: str | None = None


class LogRequest(Event):
    user_id: str = Field(min_length=1)


class LogBatchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    events: list[Event] = Field(min_length=1)


class SearchRequest(BaseModel):
    user_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)


@router.post("/log")
async def log(req: LogRequest) -> dict:
    try:
        return await get_activity_engine().log(
            req.user_id, req.app, req.action,
            target=req.target, status=req.status, detail=req.detail,
            session_id=req.session_id, meta=req.meta, ts=req.ts,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"activity.log: {e}")


@router.post("/log-batch")
async def log_batch(req: LogBatchRequest) -> dict:
    try:
        return await get_activity_engine().log_batch(req.user_id, [e.model_dump() for e in req.events])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"activity.log_batch: {e}")


@router.get("/timeline")
def timeline(
    user_id: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=200),
    app: str | None = None,
    since: str | None = None,
) -> dict:
    rows = get_activity_engine().timeline(user_id, limit=limit, app=app, since=since)
    return {"user_id": user_id, "count": len(rows), "events": rows}


@router.post("/search")
async def search(req: SearchRequest) -> dict:
    try:
        results = await get_activity_engine().search(req.user_id, req.query, req.k)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"activity.search: {e}")
    return {"user_id": req.user_id, "results": results}


@router.get("/summary")
async def summary(
    user_id: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=200),
    provider: str | None = None,
) -> dict:
    return await get_activity_engine().summary(user_id, limit=limit, provider=provider)


@router.delete("/{user_id}")
def clear(user_id: str) -> dict:
    return get_activity_engine().clear(user_id)
