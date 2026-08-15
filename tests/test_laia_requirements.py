"""Tests LAIA : besoins des apps (Brains/Engines) + Evaluation Engine."""


def test_app_requirements_seeded(client):
    r = client.get("/v1/apps/cad/requirements").json()
    assert r["app"] == "cad"
    ids = {b["id"] for b in r["required_brains"]}
    assert {"cad", "3d"}.issubset(ids)
    assert r["app_known"] is True  # cad est dans le registre écosystème fixture


def test_app_requirements_set(client):
    client.put("/v1/apps/myapp/requirements", json={"brains": ["text", "data"], "engines": ["rag"]})
    r = client.get("/v1/apps/myapp/requirements").json()
    assert {b["id"] for b in r["required_brains"]} == {"text", "data"}
    assert r["required_engines"] == ["rag"]


def test_orchestrator_uses_app_requirements(client):
    # objectif texte simple mais app=vidiapub -> le plan inclut les brains requis de l'app
    r = client.post("/v1/orchestrator/plan", json={
        "goal": "améliore ce visuel", "app": "vidiapub"}).json()
    assert r["app_requirements"] is not None
    brains = {b["id"] for b in r["brains"]}
    assert brains & {"image", "video", "vision"}  # besoins VidiaPub injectés


def test_evaluation(client):
    good = client.post("/v1/evaluate", json={
        "task": "explique le rapprochement bancaire en comptabilité",
        "output": "Le rapprochement bancaire compare le relevé de la banque et la comptabilité "
                  "pour détecter les écarts. Étapes : pointer, identifier, corriger."}).json()
    assert good["score"] > 0.4
    assert good["grade"] in {"A", "B", "C"}
    bad = client.post("/v1/evaluate", json={"task": "explique X", "output": ""}).json()
    assert bad["grade"] == "D"
