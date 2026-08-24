"""Lunziko AI — assistant intégré : grand modèle + RAG + mémoire persistante + apprentissage
continu + recherche web. C'est la BONNE architecture (vs les petits fine-tunes qui hallucinent).

5 piliers, tous fournis par l'AI Engine :
  1. GRAND MODÈLE       : qwen2.5:7b (ou tout modèle via le Provider Manager)   -> conversation/raisonnement
  2. CONNAISSANCE       : RAG sur le registre écosystème                         -> faits Lunziko exacts
  3. MÉMOIRE PERSISTANTE: module `learning` (append-only, n'oublie jamais)       -> se souvient de tout
  4. APPRENTISSAGE CONT.: learning.observe/reinforce à chaque échange            -> apprend en continu
  5. RECHERCHE WEB      : module `search` (DuckDuckGo sans clé)                   -> se renseigne sur Internet

Config (défaut = 100% local) :
  AE_LOCAL_BASE_URL=http://localhost:11434/v1  AE_LOCAL_MODEL=qwen2.5:7b
  AE_DEFAULT_PROVIDER=local  AE_EMBED_PROVIDER=local  AE_EMBED_MODEL=nomic-embed-text

Usage :
  python scripts/lunziko_ai.py --scope joe            # démo
  python scripts/lunziko_ai.py --scope joe --chat     # boucle interactive
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re

REGISTRY = r"C:\Users\Joe\Desktop\Lunziko\REGISTRE_ECOSYSTEME_LUNZIKO.md"
WEB_TRIGGERS = ("cherche", "internet", "web", "actualité", "actu", "aujourd'hui", "météo",
                "récent", "dernière", "news", "prix", "cours", "en ligne")


class LunzikoAI:
    def __init__(self, scope: str = "global") -> None:
        from ai_engine.modules.learning.engine import get_continuous_memory
        from ai_engine.modules.provider.manager import get_provider_manager
        from ai_engine.modules.rag.service import RagService
        self.scope = scope
        self.rag = RagService()
        self.ltm = get_continuous_memory()
        self.pm = get_provider_manager()

    async def index_registry(self, path: str = REGISTRY) -> int:
        md = open(path, encoding="utf-8").read()
        n = 0
        for b in re.split(r"\n(?=####\s)", md):
            m = re.match(r"####\s+(.+)", b)
            if m:
                n += 1
                await self.rag.index("lunziko", f"app{n}", b[:1600], {"app": m.group(1).strip()})
        return n

    async def _web(self, query: str) -> str:
        try:
            from ai_engine.modules.search.engine import get_search_engine
            res = await get_search_engine().search(query, k=3)
            items = res.get("results", []) if isinstance(res, dict) else res
            return "\n".join(f"- {r.get('title','')}: {r.get('snippet','')} ({r.get('url','')})"
                             for r in items[:3])
        except Exception as e:
            return f"(recherche web indisponible: {e})"

    async def chat(self, user: str, use_web: bool | None = None) -> str:
        from ai_engine.modules.provider.base import ChatMessage
        # 1) MÉMOIRE PERSISTANTE : rappel avant d'agir
        mem = await self.ltm.recall(self.scope, user, k=3)
        mem_ctx = "\n".join(f"- {x['text']}" for x in mem) if mem else "(aucun souvenir)"
        # 2) CONNAISSANCE LUNZIKO : RAG
        hits = await self.rag.search("lunziko", user, k=2)
        kb = "\n\n".join(h["text"][:700] for h in hits) if hits else ""
        # 5) RECHERCHE WEB : si demandé / détecté
        if use_web is None:
            use_web = any(t in user.lower() for t in WEB_TRIGGERS)
        web = await self._web(user) if use_web else ""
        sys = (
            "Tu es Lunziko AI, l'assistant conversationnel de l'écosystème Lunziko. Réponds de "
            "façon naturelle et EXACTE en t'appuyant sur la CONNAISSANCE et la MÉMOIRE fournies ; "
            "n'invente pas de faits Lunziko.\n\n"
            f"MÉMOIRE de l'utilisateur:\n{mem_ctx}\n\n"
            f"CONNAISSANCE LUNZIKO (registre):\n{kb}"
            + (f"\n\nRÉSULTATS WEB:\n{web}" if web else ""))
        res = await self.pm.chat([ChatMessage(role="user", content=user)], system=sys, max_tokens=200)
        # 3+4) APPRENTISSAGE CONTINU : mémorise l'échange (n'oublie jamais)
        await self.ltm.observe(self.scope, f"Question de l'utilisateur: {user}", kind="dialogue")
        return res.content.strip()

    async def remember(self, fact: str, importance: float = 0.8) -> None:
        await self.ltm.remember(self.scope, fact, importance=importance)


async def _demo(scope: str) -> None:
    ai = LunzikoAI(scope)
    print("indexation du registre...", await ai.index_registry(), "sections")
    await ai.remember("Joe est le créateur de l'écosystème Lunziko et travaille surtout sur l'AI Engine.", 0.9)
    for q, web in [("Parle-moi de Lunziko VidiaPub.", False),
                   ("Tu te souviens sur quoi je travaille ?", False),
                   ("Cherche sur internet ce qu'est le protocole MCP.", True)]:
        print(f"\n[Q] {q}")
        print("[R]", (await ai.chat(q, use_web=web))[:400])


async def _interactive(scope: str) -> None:
    ai = LunzikoAI(scope)
    print("indexation...", await ai.index_registry(), "sections. Tape 'quit' pour sortir.")
    while True:
        try:
            u = input("\nVous > ").strip()
        except EOFError:
            break
        if u.lower() in ("quit", "exit", "q"):
            break
        print("Lunziko AI >", await ai.chat(u))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", default="global")
    ap.add_argument("--chat", action="store_true", help="boucle interactive")
    a = ap.parse_args()
    os.environ.setdefault("AE_LOCAL_BASE_URL", "http://localhost:11434/v1")
    os.environ.setdefault("AE_LOCAL_MODEL", "qwen2.5:7b")
    os.environ.setdefault("AE_DEFAULT_PROVIDER", "local")
    os.environ.setdefault("AE_PROVIDER_FALLBACK", "local")
    os.environ.setdefault("AE_EMBED_PROVIDER", "local")
    os.environ.setdefault("AE_EMBED_MODEL", "nomic-embed-text")
    from ai_engine.config import get_settings
    get_settings.cache_clear()
    asyncio.run(_interactive(a.scope) if a.chat else _demo(a.scope))


if __name__ == "__main__":
    main()
