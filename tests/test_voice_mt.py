"""Test MT / traduction (V-3) — logique du moteur (backend LLM injecté, 100% offline).

Le chemin MADLAD on-device et le vrai LLM ne sont pas exercés ici (pas de modèle / pas de clé) :
on teste la validation, le choix de backend, la construction du prompt et le contrat de sortie.
"""

import asyncio

from ai_engine.modules.provider.base import ChatResult
from ai_engine.modules.voice.translate_engine import (
    LANG_NAMES, TranslationEngine, is_supported,
)


def _fake_chat_factory():
    """Retourne (chat_fn, captured) — chat_fn enregistre le system prompt reçu."""
    captured: dict = {}

    async def chat(messages, *, system=None, model=None, max_tokens=4096):
        captured["system"] = system
        captured["user"] = messages[0].content
        return ChatResult(content="[traduction simulée]", provider="fake", model="fake-1")

    return chat, captured


def test_languages_and_support():
    assert len(LANG_NAMES) == 18
    assert is_supported("ln") and is_supported("sw") and is_supported("fr")
    assert not is_supported("xx")


def test_translate_llm_backend_ok():
    chat, captured = _fake_chat_factory()
    eng = TranslationEngine(chat_fn=chat)
    out = asyncio.run(eng.translate("Bonjour le monde", source="fr", target="ln"))
    assert out["text"] == "[traduction simulée]"
    assert out["backend"] == "llm"
    assert out["source"] == "fr" and out["target"] == "ln"
    # le prompt cible mentionne la langue cible en clair
    assert "lingála" in captured["system"]
    assert "français" in captured["system"]
    assert captured["user"] == "Bonjour le monde"


def test_translate_auto_source_prompt():
    chat, captured = _fake_chat_factory()
    eng = TranslationEngine(chat_fn=chat)
    asyncio.run(eng.translate("Hello", source="auto", target="fr"))
    assert "Détecte la langue source" in captured["system"]
    assert "français" in captured["system"]


def test_same_lang_rejected():
    chat, _ = _fake_chat_factory()
    eng = TranslationEngine(chat_fn=chat)
    try:
        asyncio.run(eng.translate("x", source="fr", target="fr"))
        assert False, "aurait dû lever"
    except ValueError as e:
        assert "identiques" in str(e)


def test_unsupported_target_rejected():
    chat, _ = _fake_chat_factory()
    eng = TranslationEngine(chat_fn=chat)
    try:
        asyncio.run(eng.translate("x", source="fr", target="xx"))
        assert False, "aurait dû lever"
    except ValueError as e:
        assert "cible" in str(e)


def test_translate_status_endpoint(client):
    st = client.get("/v1/voice/translate/status").json()
    assert st["llm_fallback"] is True
    assert st["backend"] in ("madlad", "llm")
    assert len(st["languages"]) == 18


def test_translate_endpoint_same_lang_400(client):
    r = client.post("/v1/voice/translate", json={"text": "x", "source": "fr", "target": "fr"})
    assert r.status_code == 400
