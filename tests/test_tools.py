"""Tests du tool-calling (A-4b) : registre, boucle (provider factice), parseurs adaptateurs."""

import asyncio

from ai_engine.modules.provider.base import ToolCall, ToolChatResult, ToolSpec
from ai_engine.modules.provider.providers.claude import (
    build_claude_tool_body, parse_claude_tool_response,
)
from ai_engine.modules.provider.providers.openai_compat import (
    build_openai_tool_messages, parse_openai_tool_response,
)
from ai_engine.modules.tools.loop import run_tool_loop
from ai_engine.modules.tools.registry import get_tool_registry


def test_registry_has_builtins():
    reg = get_tool_registry()
    for name in ("ecosystem_search", "handoff_open_with", "data_clean_text", "ml_predict"):
        assert name in reg.names()


def test_registry_execute_offline():
    reg = get_tool_registry()
    out = asyncio.run(reg.execute("data_clean_text", {"texts": ["a", "a", ""], "min_len": 1}))
    assert "texts_out" in out  # rapport JSON


def test_tool_loop_with_fake_provider():
    """Le modèle demande un outil, on l'exécute, puis il finalise."""
    reg = get_tool_registry()
    specs = reg.specs(["data_clean_text"])
    calls = {"n": 0}

    async def fake_chat(messages, tool_specs, system):
        calls["n"] += 1
        if calls["n"] == 1:
            return ToolChatResult(provider="fake", model="m", stop_reason="tool_use",
                                  tool_calls=[ToolCall(id="t1", name="data_clean_text",
                                                       arguments={"texts": ["x", "x"]})])
        # 2e appel : le message tool est bien présent dans l'historique
        assert any(m["role"] == "tool" for m in messages)
        return ToolChatResult(provider="fake", model="m", content="Nettoyage terminé.")

    res = asyncio.run(run_tool_loop("nettoie ça", specs=specs, chat=fake_chat, execute=reg.execute))
    assert res["answer"] == "Nettoyage terminé."
    assert res["iterations"] == 2
    assert res["tool_trace"][0]["tool"] == "data_clean_text"


def test_parse_claude_tool_response():
    data = {"model": "claude-opus-4-8", "content": [
        {"type": "text", "text": "je cherche"},
        {"type": "tool_use", "id": "tu_1", "name": "ecosystem_search", "input": {"query": "bi"}}]}
    r = parse_claude_tool_response(data, "x")
    assert r.stop_reason == "tool_use"
    assert r.tool_calls[0].name == "ecosystem_search"
    assert r.tool_calls[0].arguments == {"query": "bi"}


def test_build_claude_body_tool_result():
    msgs = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "t1", "name": "f", "arguments": {"a": 1}}]},
        {"role": "tool", "tool_call_id": "t1", "name": "f", "content": "42"},
    ]
    body = build_claude_tool_body(msgs, [ToolSpec(name="f", description="d")], "sys", "m", 100)
    assert body["system"] == "sys"
    assert body["tools"][0]["input_schema"]["type"] == "object"
    assert body["messages"][-1]["content"][0]["type"] == "tool_result"


def test_parse_openai_tool_response():
    data = {"model": "gpt", "choices": [{"message": {"content": None, "tool_calls": [
        {"id": "c1", "type": "function",
         "function": {"name": "ml_predict", "arguments": '{"name":"t","text":"x"}'}}]}}]}
    r = parse_openai_tool_response(data, "chatgpt", "gpt")
    assert r.tool_calls[0].name == "ml_predict"
    assert r.tool_calls[0].arguments == {"name": "t", "text": "x"}


def test_build_openai_messages_tool_role():
    msgs = [{"role": "tool", "tool_call_id": "c1", "name": "f", "content": "ok"}]
    out = build_openai_tool_messages(msgs, "sys")
    assert out[0]["role"] == "system"
    assert out[1]["role"] == "tool" and out[1]["tool_call_id"] == "c1"


def test_tools_endpoint(client):
    t = client.get("/v1/tools").json()
    names = {s["name"] for s in t["tools"]}
    assert "ecosystem_search" in names


def test_tools_run_endpoint(client):
    r = client.post("/v1/tools/run", json={"name": "ecosystem_search",
                                           "arguments": {"query": "dashboards KPI", "k": 2}}).json()
    assert r["tool"] == "ecosystem_search"
