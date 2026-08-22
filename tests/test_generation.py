"""Test génération multimédia — dispatch/deferred, backends, activation des Brains."""

import asyncio


def test_status_offline_all_deferred():
    from ai_engine.modules.generation.engine import get_generation_engine
    st = get_generation_engine().status()
    # sans backend configuré : rien n'est servable
    assert st["servable"]["image"] is False
    assert st["servable"]["video"] is False
    assert "graphics_engine" in st["backends"]


def test_generate_deferred_lists_models_and_howto():
    from ai_engine.modules.generation.engine import get_generation_engine
    res = asyncio.run(get_generation_engine().generate("video", "un chat qui surfe"))
    assert res["status"] == "deferred" and res["kind"] == "video"
    # les modèles candidats du catalogue apparaissent (MiniMax H3, Wan…)
    ids = {m["id"] for m in res["models"]}
    assert "minimax-h3" in ids
    assert "how_to_enable" in res


def test_generate_image_models():
    from ai_engine.modules.generation.engine import get_generation_engine
    res = asyncio.run(get_generation_engine().generate("image", "un logo Lunziko"))
    ids = {m["id"] for m in res["models"]}
    assert "nano-banana" in ids


def test_unknown_kind_rejected():
    from ai_engine.modules.generation.engine import get_generation_engine
    try:
        asyncio.run(get_generation_engine().generate("hologram", "x"))
        assert False
    except ValueError:
        pass


def test_brain_activation_with_generation_backend(monkeypatch):
    import ai_engine.modules.generation.backends as gb
    # simule un backend image branché -> le Brain 'image' doit passer 'active'
    monkeypatch.setattr(gb, "backends_for", lambda kind: ["comfyui"] if kind == "image" else [])
    from ai_engine.modules.orchestrator.brains import BrainRegistry
    reg = BrainRegistry()
    image_brain = reg.get("image")
    assert image_brain["status"] == "active"
    assert image_brain.get("backend") == "comfyui"


def test_endpoints(client):
    st = client.get("/v1/generate/status").json()
    assert "backends" in st and "servable" in st
    r = client.post("/v1/generate/video", json={"prompt": "démo"})
    assert r.status_code == 200 and r.json()["status"] == "deferred"
    m = client.get("/v1/generate/models/image").json()
    assert any(x["id"] == "nano-banana" for x in m)
