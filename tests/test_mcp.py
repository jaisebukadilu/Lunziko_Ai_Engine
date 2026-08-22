"""Tests MCP (A-7) : serveur JSON-RPC + client en process (contre notre propre serveur)."""

import asyncio

from ai_engine.modules.mcp.client import MCPClient
from ai_engine.modules.mcp.server import handle
from ai_engine.modules.tools.registry import ToolRegistry


def test_initialize(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"}).json()
    assert r["result"]["protocolVersion"]
    assert r["result"]["serverInfo"]["name"] == "lunziko-ai-engine"


def test_tools_list(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"}).json()
    names = {t["name"] for t in r["result"]["tools"]}
    assert "ecosystem_search" in names
    assert all("inputSchema" in t for t in r["result"]["tools"])


def test_tools_call(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                                  "params": {"name": "data_clean_text",
                                             "arguments": {"texts": ["a", "a"]}}}).json()
    assert r["result"]["isError"] is False
    assert "texts_out" in r["result"]["content"][0]["text"]


def test_unknown_method(client):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "does/not/exist"}).json()
    assert r["error"]["code"] == -32601


def test_client_against_own_server():
    """Le client MCP consomme notre serveur via un transport en process."""
    async def in_process_send(request: dict) -> dict:
        return await handle(request)

    async def scenario():
        c = MCPClient(send=in_process_send)
        init = await c.initialize()
        assert init["serverInfo"]["name"] == "lunziko-ai-engine"
        tools = await c.list_tools()
        assert any(t["name"] == "data_clean_text" for t in tools)
        out = await c.call_tool("data_clean_text", {"texts": ["x", "x", ""]})
        assert "texts_out" in out
        # import dans un registre local : outils préfixés
        reg = ToolRegistry()
        imported = await c.import_into_registry(reg, prefix="ext")
        assert any(n.startswith("ext__") for n in imported)
        # l'outil importé est exécutable via le registre
        res = await reg.execute("ext__data_clean_text", {"texts": ["y", "y"]})
        assert "texts_out" in res

    asyncio.run(scenario())


def test_parse_sse_response():
    """Le client MCP tolère un flux SSE (Streamable HTTP, ex. serveur HF)."""
    from ai_engine.modules.mcp.client import _parse_response

    class FakeResp:
        headers = {"content-type": "text/event-stream"}
        text = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n'
        def json(self):  # non utilisé en SSE
            raise AssertionError("ne doit pas être appelé en SSE")

    out = _parse_response(FakeResp())
    assert out["result"]["tools"] == []


def test_import_hf_style_with_injected_send():
    """Import d'un serveur MCP distant (façon HF) via un transport injecté + prefix hf."""
    import asyncio

    from ai_engine.modules.mcp.client import MCPClient
    from ai_engine.modules.tools.registry import ToolRegistry

    async def hf_send(req: dict) -> dict:
        m = req.get("method")
        if m == "initialize":
            return {"jsonrpc": "2.0", "id": req["id"],
                    "result": {"serverInfo": {"name": "hf-mcp-server"}, "capabilities": {}}}
        if m == "tools/list":
            return {"jsonrpc": "2.0", "id": req["id"], "result": {"tools": [
                {"name": "model_search", "description": "Search HF models",
                 "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}}]}}
        if m == "tools/call":
            return {"jsonrpc": "2.0", "id": req["id"],
                    "result": {"content": [{"type": "text", "text": "unsloth/Qwen2.5-0.5B-Instruct"}]}}
        return {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "no"}}

    async def scenario():
        c = MCPClient(send=hf_send)
        await c.initialize()
        reg = ToolRegistry()
        imported = await c.import_into_registry(reg, prefix="hf")
        assert "hf__model_search" in imported
        res = await reg.execute("hf__model_search", {"query": "qwen"})
        assert "Qwen2.5" in res

    asyncio.run(scenario())
