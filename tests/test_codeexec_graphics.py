"""Tests Code Execution Engine (A-11, sûr par défaut) + branchement Graphics Engine."""


# --- Code Execution : Niveau 0 (safe eval) ---
def test_safe_eval_ok(client):
    r = client.post("/v1/code-exec/eval", json={"expression": "sum([x*2 for x in [1,2,3]]) if False else max(3, 7)"})
    # compréhension interdite -> on teste une expression simple autorisée
    r = client.post("/v1/code-exec/eval", json={"expression": "max(3, 7) + len([1,2,3])"}).json()
    assert r["result"] == 10


def test_safe_eval_with_vars(client):
    r = client.post("/v1/code-exec/eval", json={"expression": "a * b + 1", "variables": {"a": 4, "b": 5}}).json()
    assert r["result"] == 21


def test_safe_eval_rejects_import(client):
    r = client.post("/v1/code-exec/eval", json={"expression": "__import__('os')"})
    assert r.status_code == 422


def test_safe_eval_rejects_attr_access(client):
    r = client.post("/v1/code-exec/eval", json={"expression": "(1).__class__"})
    assert r.status_code == 422


# --- Code Execution : Niveau 1 (sandbox) désactivé par défaut ---
def test_sandbox_disabled_by_default(client):
    st = client.get("/v1/code-exec/status").json()
    assert st["safe_eval"] is True
    assert st["sandbox_enabled"] is False
    run = client.post("/v1/code-exec/run", json={"code": "print(1)"}).json()
    assert run["executed"] is False  # refus propre, pas d'exécution implicite


# --- Graphics Engine : non branché par défaut ---
def test_graphics_not_configured(client):
    st = client.get("/v1/graphics/status").json()
    assert st["configured"] is False
    assert "image" in st["graphics_backed_brains"]
    ping = client.get("/v1/graphics/ping").json()
    assert ping["configured"] is False and ping["reachable"] is False


def test_graphics_brains_declared_when_unbranched(client):
    av = client.get("/v1/graphics/brains").json()["availability"]
    assert av["3d"] == "declared"  # reste déclaré tant que non branché
    # et le Brain 3d reste 'planned' dans le registre
    assert client.get("/v1/brains/3d").json()["status"] == "planned"


def test_graphics_call_unbranched_503(client):
    r = client.post("/v1/graphics/call", json={"method": "GET", "path": "/agents"})
    assert r.status_code == 503
