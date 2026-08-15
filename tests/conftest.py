"""Configuration pytest — environnement 100% offline et déterministe.

Home temporaire par session, embedder `hash` (hors-ligne), registre = fixture réduite.
Aucune clé provider : les tests évitent les appels LLM réels (ou tolèrent leur absence).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURE_REGISTRY = Path(__file__).parent / "fixtures" / "mini_registry.md"


@pytest.fixture(scope="session", autouse=True)
def _env(tmp_path_factory):
    home = tmp_path_factory.mktemp("ae_home")
    os.environ["AI_ENGINE_HOME"] = str(home)
    os.environ["AE_EMBED_PROVIDER"] = "hash"
    os.environ["AE_REGISTRY_PATH"] = str(FIXTURE_REGISTRY)
    os.environ["AE_REGISTRY_AUTOSYNC"] = "true"
    os.environ["AE_API_KEYS"] = ""  # accès libre en test
    # purge d'un éventuel cache de settings importé avant la mise en place de l'env
    try:
        from ai_engine.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass
    yield


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from ai_engine.gateway.main import app

    with TestClient(app) as c:  # déclenche le startup (sync du registre fixture)
        yield c
