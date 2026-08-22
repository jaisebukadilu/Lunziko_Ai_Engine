"""Test Model Registry — catalogue des modèles 2026 mappés aux Brains + gouvernance licences."""


def test_catalog_has_2026_models():
    from ai_engine.modules.models.engine import get_model_registry
    reg = get_model_registry()
    ids = {m["id"] for m in reg.list_models()}
    for expected in ("qwen-3.8-max", "minimax-h3", "wan-3.0", "wan2.2-animate-14b",
                     "nano-banana", "crisperwhisper-2", "gemini-robotics-2", "prisme-ai"):
        assert expected in ids, f"{expected} manquant"


def test_restricted_flags_minimax():
    from ai_engine.modules.models.engine import get_model_registry
    h3 = get_model_registry().get("minimax-h3")
    assert h3["status"] == "restricted"
    assert "UE" in h3["restrictions"] or "US" in h3["restrictions"]


def test_by_brain_video():
    from ai_engine.modules.models.engine import get_model_registry
    vids = {m["id"] for m in get_model_registry().by_brain("video")}
    assert "minimax-h3" in vids and "wan-3.0" in vids


def test_robotics_brain_registered():
    from ai_engine.modules.models.engine import get_model_registry
    get_model_registry()  # déclenche l'enregistrement du Brain robotics
    from ai_engine.modules.orchestrator.brains import get_brain_registry
    assert get_brain_registry().get("robotics") is not None


def test_endpoints(client):
    st = client.get("/v1/model-catalog/stats").json()
    assert st["total_models"] >= 8
    r = client.get("/v1/model-catalog/usable").json()
    assert any(m["id"] == "qwen-3.8-max" for m in r)
    r = client.get("/v1/model-catalog/code-tools").json()
    assert any(t["id"] == "aider" for t in r)
    r = client.get("/v1/model-catalog/minimax-h3")
    assert r.status_code == 200
    assert client.get("/v1/model-catalog/nope").status_code == 404
