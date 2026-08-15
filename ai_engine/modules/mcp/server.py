"""Serveur MCP — JSON-RPC 2.0 exposant les outils de l'AI Engine.

Méthodes supportées : initialize, ping, tools/list, tools/call. Réutilise le ToolRegistry
(les outils intégrés + ceux importés). Sans état (chaque requête JSON-RPC est autonome).
"""

from __future__ import annotations

from ai_engine import __version__
from ai_engine.modules.mcp import MCP_PROTOCOL_VERSION
from ai_engine.modules.tools.registry import get_tool_registry

SERVER_INFO = {"name": "lunziko-ai-engine", "version": __version__}


def _ok(rid, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


async def handle(request: dict) -> dict:
    """Traite une requête JSON-RPC MCP et renvoie la réponse."""
    rid = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    reg = get_tool_registry()

    if method == "initialize":
        return _ok(rid, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
        })

    if method == "ping":
        return _ok(rid, {})

    if method == "tools/list":
        tools = [{"name": s.name, "description": s.description, "inputSchema": s.parameters}
                 for s in reg.specs()]
        return _ok(rid, {"tools": tools})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not name or name not in reg.names():
            return _err(rid, -32602, f"outil inconnu: {name}")
        text = await reg.execute(name, arguments)
        is_error = text.strip().startswith('{"error"')
        return _ok(rid, {"content": [{"type": "text", "text": text}], "isError": is_error})

    return _err(rid, -32601, f"méthode non supportée: {method}")
