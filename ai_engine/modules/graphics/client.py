"""Client REST du Lunziko Graphics Engine + mapping Brain → groupes d'endpoints.

Le Graphics Engine (dépôt séparé) est un serveur **REST FastAPI** (défaut 127.0.0.1:8000,
`X-API-Key` optionnel) : santé/agents/capabilities/engines + groupes image/imaging/video/mesh/
render/vector/pdf/asset/cad/bim/sketch/shader/workflow… Adaptateur CLIENT : `available()` (URL
configurée), `ping()`/`get()`/`post()`/`call()`. Le Graphics Engine n'est PAS modifié.
"""

from __future__ import annotations

from ai_engine.config import get_settings

# Brain LAIA -> groupes d'endpoints REST du Graphics Engine (tags réels).
BRAIN_TO_GROUPS = {
    "image": ["image", "imaging", "compose", "annotate", "raw", "vector", "pdf"],
    "vision": ["imaging", "integrity"],
    "video": ["video"],
    "3d": ["mesh", "render", "asset", "accel", "vr", "cad", "sketch"],
    "cad": ["cad", "sketch", "bim"],
    "document": ["pdf", "imaging"],
}

# Brains dont l'activation dépend du Graphics Engine.
GRAPHICS_BACKED_BRAINS = sorted(BRAIN_TO_GROUPS)


class GraphicsEngineClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        s = get_settings()
        self._base = (base_url if base_url is not None else s.ae_graphics_engine_url).rstrip("/")
        self._key = api_key if api_key is not None else s.ae_graphics_engine_api_key

    def available(self) -> bool:
        return bool(self._base)

    def _headers(self) -> dict:
        h = {"content-type": "application/json"}
        if self._key:
            h["X-API-Key"] = self._key
        return h

    def ping(self) -> dict:
        """GET /health (best-effort ; réseau requis)."""
        if not self.available():
            return {"configured": False, "reachable": False}
        try:
            import httpx
            with httpx.Client(timeout=5) as c:
                r = c.get(f"{self._base}/health", headers=self._headers())
            return {"configured": True, "reachable": r.status_code == 200,
                    "status_code": r.status_code,
                    "health": r.json() if r.status_code == 200 else None}
        except Exception as e:
            return {"configured": True, "reachable": False, "error": str(e)[:160]}

    async def call(self, method: str, path: str, body: dict | None = None) -> dict:
        """Appel générique d'un endpoint REST du Graphics Engine (GET/POST)."""
        if not self.available():
            raise RuntimeError("Graphics Engine non branché (AE_GRAPHICS_ENGINE_URL vide)")
        import httpx
        url = f"{self._base}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=120) as c:
            if method.upper() == "GET":
                r = await c.get(url, headers=self._headers(), params=body or {})
            else:
                r = await c.post(url, headers=self._headers(), json=body or {})
        if r.status_code >= 400:
            raise RuntimeError(f"graphics {r.status_code}: {r.text[:200]}")
        return r.json()


def graphics_status() -> dict:
    s = get_settings()
    return {
        "configured": bool(s.ae_graphics_engine_url),
        "base_url": s.ae_graphics_engine_url or None,
        "transport": "REST (FastAPI)",
        "graphics_backed_brains": GRAPHICS_BACKED_BRAINS,
        "brain_to_groups": BRAIN_TO_GROUPS,
        "note": "brancher via AE_GRAPHICS_ENGINE_URL (ex http://127.0.0.1:8000) ; "
                "ces Brains passent alors de 'declared' à 'active'",
    }


def graphics_brain_availability() -> dict:
    configured = bool(get_settings().ae_graphics_engine_url)
    return {b: ("active" if configured else "declared") for b in GRAPHICS_BACKED_BRAINS}
