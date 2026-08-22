"""GenerationEngine — génération multimédia via les backends branchés.

Chaque requête choisit un backend capable du type demandé. Si aucun backend n'est disponible,
la réponse est `deferred` (explicite : backends candidats + modèles du Model Registry + note GPU) —
jamais de contenu simulé. Le dispatch réel n'est effectué que pour un backend joignable.
"""

from __future__ import annotations

from ai_engine.modules.generation.backends import (
    ALL_KINDS, available_backends, backends_for,
)

# Brains génératifs concernés par chaque type de média.
KIND_TO_BRAIN = {
    "image": "image", "video": "video", "audio": "audio",
    "music": "music", "3d": "3d",
}


class GenerationEngine:
    def status(self) -> dict:
        backends = available_backends()
        servable = {k: backends_for(k) for k in ALL_KINDS}
        return {
            "backends": backends,
            "servable": {k: bool(v) for k, v in servable.items()},
            "backends_for_kind": servable,
            "note": "brancher un backend (Graphics Engine / ComfyUI / Fal / Replicate / "
                    "diffusers GPU) active la génération et fait passer le Brain de 'declared' à 'active'.",
        }

    def models_for(self, kind: str) -> list[dict]:
        """Modèles du catalogue adaptés à ce type de média (MiniMax H3, Wan, Nano Banana…)."""
        try:
            from ai_engine.modules.models.engine import get_model_registry
            reg = get_model_registry()
            brain = KIND_TO_BRAIN.get(kind, kind)
            return [{"id": m["id"], "name": m["name"], "status": m["status"],
                     "open_weights": m["open_weights"], "restrictions": m.get("restrictions", "")}
                    for m in reg.by_brain(brain)]
        except Exception:
            return []

    async def generate(self, kind: str, prompt: str, *,
                       backend: str | None = None, options: dict | None = None) -> dict:
        if kind not in ALL_KINDS:
            raise ValueError(f"type de média inconnu : {kind} (attendu {ALL_KINDS})")
        candidates = backends_for(kind)
        chosen = backend if (backend and backend in candidates) else (candidates[0] if candidates else None)

        if chosen is None:
            # Aucun backend : reporté, avec ce qu'il faut pour l'activer.
            return {
                "status": "deferred", "kind": kind, "prompt": prompt,
                "reason": "aucun backend génératif disponible pour ce type de média",
                "candidate_backends": sorted(
                    b for b, info in available_backends().items() if kind in info["kinds"]),
                "models": self.models_for(kind),
                "how_to_enable": {
                    "image": "AE_COMFYUI_URL / AE_FAL_API_KEY / OPENAI_API_KEY / Graphics Engine",
                    "video": "AE_COMFYUI_URL (MiniMax H3/Wan) / AE_FAL_API_KEY / AE_REPLICATE_API_TOKEN",
                    "audio": "AE_REPLICATE_API_TOKEN / backend audio local",
                    "music": "backend musical dédié",
                    "3d": "Graphics Engine (mesh/render/asset) / backend 3D local",
                }.get(kind, "brancher un backend adapté"),
                "note": "modèles ouverts lourds (MiniMax H3, Wan) => GPU requis ; vérifier les restrictions de licence.",
            }

        return await self._dispatch(chosen, kind, prompt, options or {})

    async def _dispatch(self, backend: str, kind: str, prompt: str, options: dict) -> dict:
        if backend == "graphics_engine":
            # Délègue au Graphics Engine (dépôt séparé) via son client REST.
            from ai_engine.modules.graphics.client import GraphicsEngineClient
            client = GraphicsEngineClient()
            group = "mesh" if kind == "3d" else "imaging"
            try:
                res = await client.call("POST", f"/{group}/generate",
                                        {"prompt": prompt, **options})
                return {"status": "generated", "kind": kind, "backend": backend, "result": res}
            except Exception as e:
                return {"status": "error", "kind": kind, "backend": backend, "detail": str(e)[:200]}

        if backend == "comfyui":
            from ai_engine.config import get_settings
            base = get_settings().ae_comfyui_url.rstrip("/")
            try:
                import httpx
                async with httpx.AsyncClient(timeout=120) as c:
                    r = await c.post(f"{base}/prompt", json={"prompt": prompt, **options})
                return {"status": "queued", "kind": kind, "backend": backend,
                        "code": r.status_code, "detail": r.text[:200]}
            except Exception as e:
                return {"status": "error", "kind": kind, "backend": backend, "detail": str(e)[:200]}

        # fal / replicate / openai_image / local_diffusers : chemins hébergés/GPU.
        return {
            "status": "backend_ready", "kind": kind, "backend": backend, "prompt": prompt,
            "note": f"backend '{backend}' configuré ; intégration d'appel dédiée à finaliser "
                    f"(clé/at présente). Dispatch réel implémenté pour graphics_engine et comfyui.",
        }


def get_generation_engine() -> GenerationEngine:
    return GenerationEngine()
