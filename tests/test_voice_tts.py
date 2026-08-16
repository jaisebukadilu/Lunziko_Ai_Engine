"""Test TTS (V-1) — statut + validation (synthèse réelle testée hors CI, nécessite voix .onnx)."""


def test_tts_status(client):
    st = client.get("/v1/voice/tts/status").json()
    assert "available" in st and isinstance(st["available"], bool)
    assert st["engine"] == "piper"
    assert isinstance(st["voices"], list)


def test_tts_unknown_voice_rejected(client):
    r = client.post("/v1/voice/tts", json={"text": "bonjour", "voice": "voix-inexistante", "lang": "fr"})
    assert r.status_code == 400  # rejet avant toute synthèse
