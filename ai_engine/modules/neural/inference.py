"""Registre des moteurs d'inférence locaux (pilier « moteur d'inférence »).

Catalogue des serveurs d'inférence supportés (compatibles OpenAI ou natifs) que l'AI Engine
peut consommer en local, et détection de l'endpoint configuré. On NE scanne PAS les ports
(offline-safe) : on rapporte le catalogue + ce qui est configuré (AE_LOCAL_BASE_URL) + le
provider natif Lunziko. La consommation réelle passe par le Provider Manager (OpenAI-compat).
"""

from __future__ import annotations

from ai_engine.config import get_settings

# Moteurs d'inférence locaux supportés (inspiration : écosystème OSS d'inférence).
INFERENCE_ENGINES = [
    {"id": "ollama", "label": "Ollama", "api": "openai-compat", "default_port": 11434,
     "note": "modèles GGUF locaux ; base URL .../v1"},
    {"id": "llamacpp", "label": "llama.cpp (server)", "api": "openai-compat", "default_port": 8080,
     "note": "serveur GGUF haute perf CPU/GPU"},
    {"id": "vllm", "label": "vLLM", "api": "openai-compat", "default_port": 8000,
     "note": "serving haut débit (paged attention)"},
    {"id": "lmstudio", "label": "LM Studio", "api": "openai-compat", "default_port": 1234,
     "note": "serveur local de bureau"},
    {"id": "triton", "label": "Triton Inference Server", "api": "kserve/openai", "default_port": 8000,
     "note": "serving multi-frameworks (TF/PyTorch/ONNX/TensorRT)"},
    {"id": "lunziko", "label": "Lunziko LLM (natif)", "api": "native", "default_port": None,
     "note": "modèle natif from scratch (paquet lunziko-llm)"},
]


def inference_status() -> dict:
    """État : catalogue + endpoint local configuré + provider natif Lunziko."""
    s = get_settings()
    configured = bool(s.ae_local_base_url)
    return {
        "engines": INFERENCE_ENGINES,
        "local_endpoint_configured": configured,
        "local_base_url": s.ae_local_base_url or None,
        "native_lunziko_configured": bool(s.ae_lunziko_llm_ckpt),
        "consumption": "via Provider Manager (endpoints OpenAI-compat) ou provider `lunziko`",
    }
