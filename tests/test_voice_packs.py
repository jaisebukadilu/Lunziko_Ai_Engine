"""Test packs de langues (V-4) — plan/install en dry-run + registre (100% offline).

Le vrai téléchargement (Piper/Whisper/MADLAD) n'est pas exercé en CI (poids lourds) :
on valide la planification par composant, la gestion des voix indisponibles, le registre.
"""

from ai_engine.modules.voice.pack_downloader import DEFAULT_COMPONENTS, install_pack, plan_pack


def test_plan_fr_default_components():
    plan = plan_pack("fr")
    assert plan["dry_run"] is True
    assert set(plan["requested"]) == set(DEFAULT_COMPONENTS)
    assert "stt" in plan["components"] and "tts" in plan["components"]
    # dry-run : statuts non "installed" (planned/skipped/present/unavailable)
    for comp in plan["components"].values():
        assert comp["status"] in ("planned", "skipped", "present", "unavailable")


def test_plan_lingala_tts_unavailable():
    # lingála n'a pas de voix Piper OSS -> TTS marqué unavailable
    plan = plan_pack("ln", components=("stt", "tts"))
    assert plan["components"]["tts"]["status"] == "unavailable"


def test_plan_unknown_pack_raises():
    try:
        plan_pack("xx")
        assert False, "aurait dû lever KeyError"
    except KeyError:
        pass


def test_endpoints_plan_and_install_dry(client):
    r = client.get("/v1/voice/packs/fr/plan")
    assert r.status_code == 200
    assert r.json()["id"] == "fr"

    r = client.post("/v1/voice/packs/fr/install", params={"dry_run": True})
    assert r.status_code == 202
    body = r.json()
    assert body["dry_run"] is True and body["installed"] is False


def test_bad_component_rejected(client):
    r = client.get("/v1/voice/packs/fr/plan", params={"components": "stt,bogus"})
    assert r.status_code == 400


def test_unknown_pack_404(client):
    r = client.post("/v1/voice/packs/zzz/install")
    assert r.status_code == 404


def test_install_registers_components(monkeypatch):
    # Simule un install réussi sans réseau : on force des composants "installed".
    import ai_engine.modules.voice.pack_downloader as pd

    monkeypatch.setattr(pd, "download_stt_model",
                        lambda m, dry_run=False: {"status": "installed", "model": m, "shared": True})
    monkeypatch.setattr(pd, "download_tts_voice",
                        lambda v, dry_run=False: {"status": "installed", "voice": v, "path": "/x"})
    res = install_pack("fr", components=("stt", "tts"), dry_run=False)
    assert res["installed"] is True
    from ai_engine.modules.voice.model_store import get_voice_store
    reg = get_voice_store()._read_registry()
    assert "fr" in reg["installed"]
    assert reg["installed"]["fr"]["components"]["stt"]["status"] == "installed"
