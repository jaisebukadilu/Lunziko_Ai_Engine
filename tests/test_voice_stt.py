"""Test STT (V-1) — statut (l'inférence réelle nécessite le modèle + audio, hors CI)."""


def test_stt_status(client):
    st = client.get("/v1/voice/stt/status").json()
    assert "available" in st and isinstance(st["available"], bool)
    assert st["engine"] == "faster-whisper"


def test_stt_requires_audio(client):
    # sans fichier audio -> 422 (validation FastAPI)
    r = client.post("/v1/voice/stt", data={"lang": "auto"})
    assert r.status_code == 422
