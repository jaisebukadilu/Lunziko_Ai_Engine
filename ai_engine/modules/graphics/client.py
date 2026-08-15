"""Client JSON-RPC du Lunziko Graphics Engine + mapping Brain → agents.

Adaptateur : `available()` (URL configurée), `ping()` (best-effort), `call(method, params)`.
Le mapping associe les capacités des Brains multimédias aux agents du Graphics Engine, ce qui
permet à LAIA d'activer ces Brains lorsque le moteur est branché.
"""

from __future__ import annotations

import itertools

from ai_engine.config import get_settings

# Brain LAIA -> agents du Graphics Engine sollicités.
BRAIN_TO_AGENTS = {
    "image": ["imaging", "vector"],
    "vision": ["imaging"],
    "video": ["imaging", "asset"],
    "3d": ["asset", "sketch", "cad", "bim"],
    "cad": ["cad", "sketch", "bim"],
    "document": ["pdf", "imaging"],
}

# Brains dont l'activation dépend du Graphics Engine.
GRAPHICS_BACKED_BRAINS = sorted(BRAIN_TO_AGENTS)


class GraphicsEngineClient:
    def __init__(self, base_url: str | None = None) -> None:
        self._base = (base_url if base_url is not None else get_settings().ae_graphics_engine_url).rstrip("/")
        self._ids = itertools.count(1)

    def available(self) -> bool:
        return bool(self._base)

    def ping(self) -> dict:
        """Best-effort : tente un appel JSON-RPC léger. Réseau requis (sinon reachable=False)."""
        if not self.available():
            return {"configured": False, "reachable": False}
        try:
            import httpx
            req = {"jsonrpc": "2.0", "id": next(self._ids), "method": "system.status", "params": {}}
            with httpx.Client(timeout=5) as c:
                r = c.post(self._base, json=req)
            return {"configured": True, "reachable": r.status_code == 200,
                    "status_code": r.status_code}
        except Exception as e:
            return {"configured": True, "reachable": False, "error": str(e)[:120]}

    async def call(self, method: str, params: dict | None = None) -> dict:
        if not self.available():
            raise RuntimeError("Graphics Engine non branché (AE_GRAPHICS_ENGINE_URL vide)")
        import httpx
        req = {"jsonrpc": "2.0", "id": next(self._ids), "method": method, "params": params or {}}
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(self._base, json=req)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"graphics {method}: {data['error']}")
        return data.get("result", {})


def graphics_status() -> dict:
    client = GraphicsEngineClient()
    configured = client.available()
    return {
        "configured": configured,
        "base_url": get_settings().ae_graphics_engine_url or None,
        "graphics_backed_brains": GRAPHICS_BACKED_BRAINS,
        "brain_to_agents": BRAIN_TO_AGENTS,
        "note": "brancher via AE_GRAPHICS_ENGINE_URL ; ces Brains passent alors de 'declared' à 'active'",
    }


def graphics_brain_availability() -> dict:
    """Statut effectif des Brains dépendant du Graphics Engine (active si branché)."""
    configured = GraphicsEngineClient().available()
    return {b: ("active" if configured else "declared") for b in GRAPHICS_BACKED_BRAINS}
