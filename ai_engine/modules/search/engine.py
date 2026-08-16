"""SearchEngine — recherche web multi-backend (DuckDuckGo sans clé / Google CSE optionnel)."""

from __future__ import annotations

import asyncio
import importlib.util

from ai_engine.config import get_settings


def _ddg_available() -> bool:
    return importlib.util.find_spec("ddgs") is not None or importlib.util.find_spec("duckduckgo_search") is not None


def _search_ddg(query: str, k: int) -> list[dict]:
    try:
        from ddgs import DDGS
    except Exception:
        from duckduckgo_search import DDGS  # ancien nom du paquet
    out = []
    for r in DDGS().text(query, max_results=k):
        out.append({"title": r.get("title", ""), "url": r.get("href") or r.get("url", ""),
                    "snippet": r.get("body", "")})
    return out


async def _search_google(query: str, k: int) -> list[dict]:
    import httpx
    s = get_settings()
    params = {"key": s.ae_google_api_key, "cx": s.ae_google_cse_id, "q": query, "num": min(k, 10)}
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get("https://www.googleapis.com/customsearch/v1", params=params)
    r.raise_for_status()
    return [{"title": i.get("title", ""), "url": i.get("link", ""), "snippet": i.get("snippet", "")}
            for i in r.json().get("items", [])]


class SearchEngine:
    def available_backends(self) -> list[str]:
        s = get_settings()
        b = []
        if _ddg_available():
            b.append("duckduckgo")
        if s.ae_google_api_key and s.ae_google_cse_id:
            b.append("google")
        return b

    def _resolve(self, backend: str | None) -> str:
        s = get_settings()
        choice = backend or s.ae_search_backend
        avail = self.available_backends()
        if choice in avail:
            return choice
        if choice == "auto":
            if "google" in avail:
                return "google"
            if "duckduckgo" in avail:
                return "duckduckgo"
        # dernier recours
        return avail[0] if avail else ""

    def status(self) -> dict:
        return {"available_backends": self.available_backends(),
                "default": get_settings().ae_search_backend,
                "note": "DuckDuckGo sans clé ; Google CSE si AE_GOOGLE_API_KEY + AE_GOOGLE_CSE_ID"}

    async def search(self, query: str, *, k: int = 5, backend: str | None = None) -> dict:
        chosen = self._resolve(backend)
        if not chosen:
            return {"backend": None, "results": [],
                    "error": "aucun backend de recherche disponible (installer `ddgs` ou configurer Google CSE)"}
        if chosen == "google":
            results = await _search_google(query, k)
        else:
            results = await asyncio.to_thread(_search_ddg, query, k)  # ddgs est bloquant
        return {"backend": chosen, "query": query, "results": results[:k]}


def get_search_engine() -> SearchEngine:
    return SearchEngine()
