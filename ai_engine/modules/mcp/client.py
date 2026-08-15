"""Client MCP — consomme un serveur MCP externe et importe ses outils localement.

Transport injectable : par défaut HTTP (httpx vers une URL JSON-RPC), mais tout `send`
async (dict→dict) convient (utile pour les tests en process). `import_into_registry` enregistre
les outils distants dans le ToolRegistry local (préfixés) : les agents peuvent alors les appeler.
"""

from __future__ import annotations

import itertools
from typing import Awaitable, Callable

from ai_engine.modules.provider.base import ToolSpec

Send = Callable[[dict], Awaitable[dict]]


def _http_send(base_url: str) -> Send:
    import httpx

    async def send(request: dict) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(base_url, json=request)
        resp.raise_for_status()
        return resp.json()

    return send


class MCPClient:
    def __init__(self, *, base_url: str | None = None, send: Send | None = None) -> None:
        if send is None and base_url is None:
            raise ValueError("fournir base_url ou send")
        self._send = send or _http_send(base_url)  # type: ignore[arg-type]
        self._ids = itertools.count(1)

    async def _call(self, method: str, params: dict | None = None) -> dict:
        req = {"jsonrpc": "2.0", "id": next(self._ids), "method": method, "params": params or {}}
        resp = await self._send(req)
        if "error" in resp:
            raise RuntimeError(f"MCP {method}: {resp['error']}")
        return resp.get("result", {})

    async def initialize(self) -> dict:
        return await self._call("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "lunziko-ai-engine", "version": "0"}})

    async def list_tools(self) -> list[dict]:
        return (await self._call("tools/list")).get("tools", [])

    async def call_tool(self, name: str, arguments: dict) -> str:
        res = await self._call("tools/call", {"name": name, "arguments": arguments})
        parts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        return "\n".join(parts)

    async def import_into_registry(self, registry, *, prefix: str = "mcp") -> list[str]:
        """Enregistre les outils distants dans le registre local. Retourne les noms importés."""
        imported = []
        for t in await self.list_tools():
            remote_name = t["name"]
            local_name = f"{prefix}__{remote_name}"

            def make_handler(rn):
                async def handler(args: dict):
                    return await self.call_tool(rn, args)
                return handler

            spec = ToolSpec(name=local_name,
                            description=f"[MCP:{prefix}] {t.get('description', '')}",
                            parameters=t.get("inputSchema", {"type": "object", "properties": {}}))
            registry.register(spec, make_handler(remote_name))
            imported.append(local_name)
        return imported
