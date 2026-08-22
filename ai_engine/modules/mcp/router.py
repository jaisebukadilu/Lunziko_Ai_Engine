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
    headers: dict = Field(default_factory=dict)   # ex. {"Authorization": "Bearer <token>"}
    token: str = ""                                # raccourci -> Authorization: Bearer <token>


def _with_token(headers: dict, token: str) -> dict:
    h = dict(headers or {})
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


@router.post("/v1/mcp/import")
async def mcp_import(req: ImportRequest) -> dict:
    """Importe les outils d'un serveur MCP externe dans le registre local (agents/act)."""
    from ai_engine.modules.mcp.client import MCPClient
    from ai_engine.modules.tools.registry import get_tool_registry

    try:
        client = MCPClient(base_url=req.base_url, headers=_with_token(req.headers, req.token))
        await client.initialize()
        imported = await client.import_into_registry(get_tool_registry(), prefix=req.prefix)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mcp.import: {e}")
    return {"imported": imported, "count": len(imported)}


@router.post("/v1/mcp/import-hf")
async def mcp_import_hf(token: str = "") -> dict:
    """Importe les outils du serveur MCP Hugging Face (modèles/datasets) dans le registre.

    Token pris dans la requête sinon dans la config (AE_HF_MCP_TOKEN). Préfixe `hf`.
    """
    from ai_engine.config import get_settings
    from ai_engine.modules.mcp.client import MCPClient
    from ai_engine.modules.tools.registry import get_tool_registry

    s = get_settings()
    tok = token or s.ae_hf_mcp_token
    if not tok:
        raise HTTPException(status_code=400,
                            detail="token HF requis (AE_HF_MCP_TOKEN ou paramètre token)")
    try:
        client = MCPClient(base_url=s.ae_hf_mcp_url, headers={"Authorization": f"Bearer {tok}"})
        await client.initialize()
        imported = await client.import_into_registry(get_tool_registry(), prefix="hf")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"mcp.import-hf: {e}")
    return {"server": s.ae_hf_mcp_url, "imported": imported, "count": len(imported)}
