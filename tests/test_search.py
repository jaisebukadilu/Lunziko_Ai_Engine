"""Tests du Search Engine web (backend keyless mocké — pas d'appel réseau en test)."""

import ai_engine.modules.search.engine as se


def test_search_status(client):
    st = client.get("/v1/search/status").json()
    assert "available_backends" in st and isinstance(st["available_backends"], list)
    assert "duckduckgo" in st["available_backends"]  # ddgs installé (extra dev)


def test_web_search_tool_registered(client):
    names = {t["name"] for t in client.get("/v1/tools").json()["tools"]}
    assert "web_search" in names


def test_search_dispatch_mocked(client, monkeypatch):
    monkeypatch.setattr(se, "_search_ddg",
                        lambda q, k: [{"title": "Lunziko", "url": "https://lunziko.app", "snippet": "x"}])
    r = client.post("/v1/search", json={"query": "lunziko ecosystem", "k": 2}).json()
    assert r["backend"] == "duckduckgo"
    assert r["results"][0]["url"] == "https://lunziko.app"


def test_search_via_tool_mocked(client, monkeypatch):
    monkeypatch.setattr(se, "_search_ddg",
                        lambda q, k: [{"title": "T", "url": "u", "snippet": "s"}])
    r = client.post("/v1/tools/run", json={"name": "web_search", "arguments": {"query": "test"}}).json()
    assert "T" in r["result"]  # résultat JSON contenant le titre
