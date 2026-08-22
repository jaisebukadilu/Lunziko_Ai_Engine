#!/usr/bin/env python3
"""Auto-test d'intégration Ollama pour Lunziko AI Engine.

Exerce, en RÉEL contre Ollama (http://localhost:11434), les capacités qui peuvent tourner
100 % en local : chat multi-modèles, embeddings, RAG bout-en-bout, analyse de code,
disponibilité provider, tool-calling. Affiche un rapport PASS/FAIL.

Lancement : .venv/Scripts/python.exe scripts/ollama_selftest.py
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import urllib.request

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "qwen2.5:7b")

# --- Config : tout en local via Ollama, AVANT d'importer l'AI Engine -----
os.environ.setdefault("AI_ENGINE_HOME", tempfile.mkdtemp(prefix="ae_ollama_"))
os.environ["AE_LOCAL_BASE_URL"] = f"{OLLAMA}/v1"
os.environ["AE_LOCAL_MODEL"] = CHAT_MODEL
os.environ["AE_DEFAULT_PROVIDER"] = "local"
os.environ["AE_PROVIDER_FALLBACK"] = "local"
os.environ["AE_EMBED_PROVIDER"] = "local"
os.environ["AE_EMBED_MODEL"] = "nomic-embed-text"
os.environ["AE_REGISTRY_AUTOSYNC"] = "false"

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def ollama_up() -> list[str]:
    import json
    with urllib.request.urlopen(f"{OLLAMA}/v1/models", timeout=8) as r:
        data = json.loads(r.read().decode())
    return [m["id"] for m in data.get("data", [])]


async def main() -> int:
    try:
        models = ollama_up()
    except Exception as e:
        print(f"Ollama injoignable sur {OLLAMA} : {e}")
        return 2
    print(f"Ollama OK — {len(models)} modèles : {', '.join(models)}\n")

    from ai_engine.config import get_settings
    get_settings.cache_clear()

    from ai_engine.modules.provider.base import ChatMessage
    from ai_engine.modules.provider.manager import ProviderManager

    pm = ProviderManager()

    # T1 — provider local disponible
    check("provider local disponible", "local" in pm.list_available(), str(pm.list_available()))

    # T2 — chat modèle par défaut (qwen2.5)
    r = await pm.chat([ChatMessage(role="user", content="Réponds en un mot : capitale de la France ?")],
                      provider="local", max_tokens=30)
    check(f"chat {CHAT_MODEL}", "paris" in r.content.lower(), r.content.strip()[:60])

    # T3 — chat autre modèle si présent (glm4)
    if "glm4:latest" in models:
        r = await pm.chat([ChatMessage(role="user", content="Dis 'bonjour' en lingála (un mot).")],
                          provider="local", model="glm4:latest", max_tokens=30)
        check("chat glm4:latest", bool(r.content.strip()), r.content.strip()[:60])

    # T4 — modèle de raisonnement si présent (deepseek-r1)
    if "deepseek-r1:7b" in models:
        r = await pm.chat([ChatMessage(role="user", content="2+2 = ? Réponds par le nombre.")],
                          provider="local", model="deepseek-r1:7b", max_tokens=200)
        check("chat deepseek-r1:7b", "4" in r.content, r.content.strip()[-40:])

    # T5 — embeddings via nomic-embed-text
    from ai_engine.modules.embeddings.manager import EmbeddingManager
    em = EmbeddingManager()
    check("embedder actif = local", em.active_name == "local", em.active_name)
    er = await em.embed(["Bonjour le monde", "facturation client trimestre"])
    dim = len(er.vectors[0]) if hasattr(er, "vectors") else len(er[0])
    vecs = er.vectors if hasattr(er, "vectors") else er
    check("embeddings nomic (2 vecteurs)", len(vecs) == 2 and dim >= 256, f"dim={dim}")

    # T6 — RAG bout-en-bout (embeddings locaux + génération locale)
    from ai_engine.modules.rag.service import RagService
    rag = RagService()
    await rag.index("ollama_test", "d1", "Lunziko One est la suite ERP métier de l'écosystème Lunziko.")
    await rag.index("ollama_test", "d2", "Lunziko BI est la couche analytique et de tableaux de bord.")
    await rag.index("ollama_test", "d3", "Lunziko Yekoli est la plateforme d'apprentissage des langues.")
    hits = await rag.search("ollama_test", "Quelle app fait de l'analytique ?", k=2)
    check("RAG search (BI en tête)", bool(hits) and hits[0]["id"].startswith("d2"),
          str([h["id"] for h in hits]))
    q = await rag.query("ollama_test", "Quelle application Lunziko sert à l'apprentissage des langues ?", k=3)
    ans_obj = q["answer"] if isinstance(q, dict) else q
    ans = getattr(ans_obj, "content", str(ans_obj))
    check("RAG query (génération locale)", "yekoli" in ans.lower(), ans.strip()[:80])

    # T7 — analyse de code via modèle local
    from ai_engine.modules.code.engine import CodeEngine
    ce = CodeEngine()
    cr = await ce.analyze("def add(a,b):\n  return a-b\n", question="Y a-t-il un bug ?")
    txt = cr.get("result") or cr.get("analysis") or str(cr)
    check("code analyze (local)", bool(txt and len(str(txt)) > 10), str(txt)[:80])

    # T8 — tool-calling supporté par le provider local (OpenAI-compat)
    check("provider local tool-capable", "local" in pm.tool_capable(), str(pm.tool_capable()))

    # --- Rapport ---------------------------------------------------------
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n=== RÉSULTAT OLLAMA : {passed}/{total} tests réussis ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
