"""Registre des backends génératifs — détection de disponibilité par type de média.

Backends supportés (tous OPTIONNELS, détectés à l'exécution) :
  * graphics_engine : le Lunziko Graphics Engine branché (AE_GRAPHICS_ENGINE_URL) — image/3d ;
  * comfyui         : serveur ComfyUI (AE_COMFYUI_URL) — image/vidéo (ex. MiniMax H3, Wan) ;
  * fal             : API Fal.ai hébergée (AE_FAL_API_KEY) — image/vidéo ;
  * replicate       : API Replicate (AE_REPLICATE_API_TOKEN) — image/vidéo/audio ;
  * openai_image    : DALL·E via OPENAI_API_KEY — image ;
  * local_diffusers : `diffusers` + torch + CUDA présents localement — image/vidéo.

Aucun backend n'est requis pour démarrer ; leur absence => génération `deferred`.
"""

from __future__ import annotations

import importlib.util

from ai_engine.config import get_settings

# Capacités par backend (types de média servis).
BACKEND_KINDS = {
    "graphics_engine": {"image", "3d"},
    "comfyui": {"image", "video"},
    "fal": {"image", "video"},
    "replicate": {"image", "video", "audio"},
    "openai_image": {"image"},
    "local_diffusers": {"image", "video"},
}

ALL_KINDS = ("image", "video", "audio", "music", "3d")


def _cuda_diffusers() -> bool:
    if importlib.util.find_spec("diffusers") is None or importlib.util.find_spec("torch") is None:
        return False
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def available_backends() -> dict[str, dict]:
    """État de chaque backend : disponible + types de média servis."""
    s = get_settings()
    out: dict[str, dict] = {}

    def add(name: str, ok: bool, detail: str = "") -> None:
        out[name] = {"available": ok, "kinds": sorted(BACKEND_KINDS.get(name, set())),
                     "detail": detail}

    # Graphics Engine : joignable ?
    ge_ok = bool(s.ae_graphics_engine_url)
    add("graphics_engine", ge_ok, "branché" if ge_ok else "AE_GRAPHICS_ENGINE_URL non défini")

    add("comfyui", bool(s.ae_comfyui_url), s.ae_comfyui_url or "AE_COMFYUI_URL non défini")
    add("fal", bool(s.ae_fal_api_key), "clé présente" if s.ae_fal_api_key else "AE_FAL_API_KEY non défini")
    add("replicate", bool(s.ae_replicate_api_token),
        "token présent" if s.ae_replicate_api_token else "AE_REPLICATE_API_TOKEN non défini")
    add("openai_image", bool(s.openai_api_key),
        "clé OpenAI présente" if s.openai_api_key else "OPENAI_API_KEY non défini")
    add("local_diffusers", _cuda_diffusers(),
        "diffusers+CUDA" if _cuda_diffusers() else "diffusers/torch/CUDA absent")
    return out


def backends_for(kind: str) -> list[str]:
    """Backends disponibles capables de servir ce type de média."""
    avail = available_backends()
    return [name for name, info in avail.items()
            if info["available"] and kind in BACKEND_KINDS.get(name, set())]


def kind_servable(kind: str) -> bool:
    return bool(backends_for(kind))
