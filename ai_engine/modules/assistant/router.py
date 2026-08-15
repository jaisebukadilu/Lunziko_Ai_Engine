"""Routeur assistant — REST (assistance, agents, sessions, contrat UI) + WebSocket (UI future).

`router`    : routes HTTP (montées avec l'auth clé API du gateway).
`ws_router` : WebSocket, monté sans l'auth d'en-tête (auth optionnelle par token de requête).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from ai_engine.config import get_settings
from ai_engine.modules.assistant.engine import get_app_assistant
from ai_engine.modules.assistant.session import get_session_store
from ai_engine.modules.assistant.ui_contract import ui_contract

router = APIRouter(prefix="/v1/assistant", tags=["assistant"])
ws_router = APIRouter(tags=["assistant"])


class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    user_id: str | None = None
    provider: str | None = None
    max_tokens: int = Field(default=1024, ge=1, le=128000)


class TeamRequest(BaseModel):
    task: str = Field(min_length=1)
    user_id: str | None = None
    provider: str | None = None


class AgentRequest(BaseModel):
    role: str = Field(min_length=1)
    description: str = ""


class SessionRequest(BaseModel):
    app: str = Field(min_length=1)
    user_id: str | None = None
    title: str = ""


# --- Scope & assistance ---------------------------------------------------
@router.get("/{app}/scope")
def scope(app: str) -> dict:
    return get_app_assistant().scope(app)


@router.get("/{app}/ui-contract")
def contract(app: str) -> dict:
    return ui_contract(app)


@router.post("/{app}/ask")
async def ask(app: str, req: AskRequest) -> dict:
    return await get_app_assistant().ask(
        app, req.query, user_id=req.user_id, provider=req.provider, max_tokens=req.max_tokens
    )


@router.post("/{app}/team")
async def team(app: str, req: TeamRequest) -> dict:
    return await get_app_assistant().team_run(
        app, req.task, user_id=req.user_id, provider=req.provider
    )


# --- Agents (≤ 5 par application) ----------------------------------------
@router.get("/{app}/agents")
def list_agents(app: str) -> dict:
    a = get_app_assistant()
    return {"app": app, "max": 5, "agents": a.list_agents(app)}


@router.post("/{app}/agents")
def create_agent(app: str, req: AgentRequest) -> dict:
    try:
        return get_app_assistant().create_agent(app, req.role, req.description)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{app}/agents/{agent_id}")
def delete_agent(app: str, agent_id: str) -> dict:
    return {"deleted": get_app_assistant().delete_agent(app, agent_id)}


# --- Sessions (interface future) -----------------------------------------
@router.post("/sessions")
def create_session(req: SessionRequest) -> dict:
    return get_session_store().create(req.app, req.user_id, req.title)


@router.get("/sessions/{sid}")
def get_session(sid: str) -> dict:
    rec = get_session_store().get(sid)
    if rec is None:
        raise HTTPException(status_code=404, detail="session inconnue")
    return rec


@router.get("/{app}/sessions")
def list_sessions(app: str) -> dict:
    return {"app": app, "sessions": get_session_store().list(app)}


# --- WebSocket (canal temps réel pour l'interface visuelle) ---------------
def _ws_authorized(token: str | None) -> bool:
    keys = get_settings().api_keys
    return (not keys) or (token in keys)  # libre en dev si aucune clé configurée


@ws_router.websocket("/v1/assistant/{app}/ws")
async def assistant_ws(websocket: WebSocket, app: str) -> None:
    token = websocket.query_params.get("token")
    if not _ws_authorized(token):
        await websocket.close(code=4401)  # non autorisé
        return
    await websocket.accept()
    assistant = get_app_assistant()
    sessions = get_session_store()

    # Événement d'accueil : le frontend reçoit la zone de compétence + le contrat UI.
    await websocket.send_json({"type": "ready", "app": app, "scope": assistant.scope(app),
                               "ui": ui_contract(app)})
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") != "message":
                await websocket.send_json({"type": "error", "detail": "type attendu: 'message'"})
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                await websocket.send_json({"type": "error", "detail": "contenu vide"})
                continue
            sid = msg.get("session_id")
            if sid:
                sessions.append(sid, "user", content)
            res = await assistant.ask(app, content, user_id=msg.get("user_id"))
            if res.get("answer"):
                if sid:
                    sessions.append(sid, "assistant", res["answer"]["content"])
                await websocket.send_json({"type": "answer", **res})
            else:
                await websocket.send_json({"type": "error", "detail": res.get("error"),
                                           "in_scope": res["in_scope"], "redirect": res.get("redirect")})
    except WebSocketDisconnect:
        return
