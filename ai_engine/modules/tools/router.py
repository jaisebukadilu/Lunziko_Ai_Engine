"""Routeur tools — /v1/tools (liste), /v1/tools/run (exécution directe), /v1/agent/act (boucle)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.provider.base import ProviderError
from ai_engine.modules.provider.manager import get_provider_manager
from ai_engine.modules.tools.loop import run_tool_loop
from ai_engine.modules.tools.registry import get_tool_registry

router = APIRouter(prefix="/v1", tags=["tools"])


class RunToolRequest(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict = Field(default_factory=dict)


class ActRequest(BaseModel):
    query: str = Field(min_length=1)
    tools: list[str] | None = None      # None => tous les outils
    provider: str | None = None
    system: str | None = None
    max_iters: int = Field(default=5, ge=1, le=12)


@router.get("/tools")
def list_tools() -> dict:
    reg = get_tool_registry()
    pm = get_provider_manager()
    return {"tools": [s.model_dump() for s in reg.specs()],
            "tool_capable_providers": pm.tool_capable()}


@router.post("/tools/run")
async def run_tool(req: RunToolRequest) -> dict:
    result = await get_tool_registry().execute(req.name, req.arguments)
    return {"tool": req.name, "result": result}


@router.post("/agent/act")
async def act(req: ActRequest) -> dict:
    reg = get_tool_registry()
    specs = reg.specs(req.tools)
    pm = get_provider_manager()

    async def chat(messages, tool_specs, system):
        return await pm.chat_with_tools(messages, tool_specs, provider=req.provider, system=system)

    try:
        return await run_tool_loop(
            req.query, specs=specs, chat=chat, execute=reg.execute,
            system=req.system, max_iters=req.max_iters,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
