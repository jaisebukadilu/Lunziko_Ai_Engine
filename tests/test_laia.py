"""Tests LAIA AI-CORE : Brain/Engine registry, orchestrator plan, blackboard, validation."""


def test_brains_catalog(client):
    b = client.get("/v1/brains").json()
    ids = {x["id"] for x in b["brains"]}
    assert {"text", "reasoning", "code", "data", "ui_ux"}.issubset(ids)
    # actifs listés avant les planned
    active = client.get("/v1/brains", params={"status": "active"}).json()
    assert all(x["status"] == "active" for x in active["brains"])


def test_brain_resolve(client):
    r = client.post("/v1/brains/resolve", json={"query": "génère et corrige du code python"}).json()
    assert r["brains"] and r["brains"][0]["id"] == "code"


def test_brain_capabilities_and_register(client):
    caps = client.get("/v1/brains/data/capabilities").json()
    assert "forecast" in caps["capabilities"]
    client.post("/v1/brains/register", json={"id": "custom", "name": "Custom Brain",
                                             "capabilities": ["x"], "status": "active"})
    assert client.get("/v1/brains/custom").json()["name"] == "Custom Brain"


def test_engines_map_modules(client):
    e = client.get("/v1/engines").json()
    ids = {x["id"] for x in e["engines"]}
    assert {"inference", "rag", "memory", "context", "tool", "automation"}.issubset(ids)
    assert client.get("/v1/engines/rag").json()["module"] == "rag"


def test_orchestrator_plan_decomposes(client):
    r = client.post("/v1/orchestrator/plan", json={
        "goal": "analyse mes données et rédige un rapport"}).json()
    assert "task_id" in r
    assert len(r["plan"]) >= 2  # deux sous-tâches (analyse / rédige)
    brains = {b["id"] for b in r["brains"]}
    assert brains & {"data", "text", "document", "reasoning"}
    # la tâche est bien sur le blackboard
    task = client.get("/v1/blackboard/tasks/" + r["task_id"]).json()
    assert task["goal"].startswith("analyse")
    assert len(task["plan"]) == len(r["plan"])


def test_validation(client):
    ok = client.post("/v1/validate", json={"type": "code", "content": "def f(x):\n    return x + 1"}).json()
    assert ok["valid"] is True
    bad = client.post("/v1/validate", json={"type": "code", "content": "def f(x): return ("}).json()
    assert bad["valid"] is False
    types = client.get("/v1/validate/types").json()["types"]
    assert "ui" in types and "data" in types
