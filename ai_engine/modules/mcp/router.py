"""Routeur MCP — POST /mcp (JSON-RPC 2.0) + GET /mcp (info) + import d'un serveur externe."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_engine.modules.mcp import MCP_PROTOCOL_VERSION
from ai_engine.modules.mcp.server import SERVER_INFO, handle

router = APIRouter(tags=["mcp"])


@router.get("/mcp")
def mcp_info() -> dict:
    return {"protocol": "mcp", "version": MCP_PROTOCOL_VERSION, "serverInfo": SERVER_INFO,
            "endpoint": "POST /mcp (JSON-RPC 2.0)",
            "methods": ["initialize", "ping", "tools/list", "tools/call"]}


@router.post("/mcp")
async def mcp_jsonrpc(request: dict) -> dict:
    return await handle(request)


class ImportRequest(BaseModel):
    base_url: str = Field(min_length=1)
    prefix: str = "mcp"


@router.post("/v1/mcp/import")
async def mcp_import(req: ImportRequest) -> dict:
    """Importe les outils d'un serveur MCP externe dans le registre local (agents/act)."""
    from ai_engine.modules.mcp.client import MCPClient
    from ai_engine.modules.tools.registry import get_tool_registry

    try:
        client = MCPClient(base_url=req.base_url)
        await client.initialize()
        imported = await client.import_into_registry(get_tool_registry(), prefix=req.prefix)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mcp.import: {e}")
    return {"imported": imported, "count": len(imported)}
