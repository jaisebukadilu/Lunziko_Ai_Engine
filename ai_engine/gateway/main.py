"""Lunziko AI Engine — Gateway (point d'entrée FastAPI, autonome).

Lancement : uvicorn ai_engine.gateway.main:app --reload --port 8770
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_engine import __version__
from ai_engine.config import get_settings
from ai_engine.core.registry import get_storage
from ai_engine.gateway.auth import require_api_key, require_bearer_or_key
from ai_engine.modules.actions.router import router as actions_router
from ai_engine.modules.activity.router import router as activity_router
from ai_engine.modules.agents.router import router as agent_router
from ai_engine.modules.automation.router import router as automation_router
from ai_engine.modules.assistant.router import router as assistant_router, ws_router as assistant_ws_router
from ai_engine.modules.catalog.router import router as catalog_router
from ai_engine.modules.code.router import router as code_router
from ai_engine.modules.codeexec.router import router as codeexec_router
from ai_engine.modules.connectors.router import router as connectors_router
from ai_engine.modules.context.router import router as context_router
from ai_engine.modules.graphics.router import router as graphics_router
from ai_engine.modules.feedback.router import router as feedback_router
from ai_engine.modules.data.router import router as data_router
from ai_engine.modules.ecosystem.router import router as ecosystem_router
from ai_engine.modules.handoff.router import router as handoff_router
from ai_engine.modules.openai_api.router import router as openai_router
from ai_engine.modules.embeddings.router import router as embeddings_router
from ai_engine.modules.knowledge.router import router as knowledge_router
from ai_engine.modules.mcp.router import router as mcp_router
from ai_engine.modules.memory.router import router as memory_router
from ai_engine.modules.neural.router import router as neural_router
from ai_engine.modules.orchestrator.router import router as orchestrator_router
from ai_engine.modules.provider.router import router as provider_router
from ai_engine.modules.rag.router import router as rag_router
from ai_engine.modules.safety.router import router as safety_router
from ai_engine.modules.tools.router import router as tools_router
from ai_engine.modules.voice.model_store import get_voice_store
from ai_engine.modules.voice.router import router as voice_router
from ai_engine.modules.workflows.router import router as workflow_router

settings = get_settings()

app = FastAPI(
    title="Lunziko AI Engine",
    version=__version__,
    description="IA autonome (gateway, providers, mémoire, RAG, agents, voix). Indépendante de Platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup() -> None:
    settings.home.mkdir(parents=True, exist_ok=True)
    get_storage()          # initialise le StoragePort (SQLite par défaut)
    get_voice_store()      # initialise le magasin voix
    # Analyse du registre maître au lancement (règle de gouvernance de l'écosystème).
    if settings.ae_registry_autosync:
        try:
            from ai_engine.modules.ecosystem.engine import get_ecosystem_engine

            res = await get_ecosystem_engine().sync()
            if res.get("synced"):
                print(f"[ecosystem] registre v{res.get('version')} synchronisé : "
                      f"{res.get('count')} applications indexées ({res.get('embedder')}).")
            else:
                print(f"[ecosystem] registre non synchronisé : {res.get('reason')}.")
        except Exception as e:  # non fatal : l'AI Engine démarre même sans registre
            print(f"[ecosystem] sync ignorée ({e}).")


@app.get("/", tags=["system"])
def root() -> dict:
    return {"service": "lunziko-ai-engine", "version": __version__, "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict:
    from ai_engine.modules.embeddings.manager import get_embedding_manager
    from ai_engine.modules.memory.crypto import get_cipher
    from ai_engine.modules.voice.voices import CANONICAL_VOICES

    return {
        "status": "ok",
        "service": "lunziko-ai-engine",
        "version": __version__,
        "independent_of_platform": True,
        "home": str(settings.home),
        "storage_backend": settings.ae_storage_backend,
        "vector_backend": settings.ae_vector_backend,
        "embedder": get_embedding_manager().active_name,
        "memory_cipher": get_cipher().mode,
        "voices": len(CANONICAL_VOICES),
        "packs_installed": sorted(get_voice_store().installed_ids()),
        "modules": {
            "provider": True, "embeddings": True, "rag": True,
            "memory": True, "knowledge": True, "agents": True,
            "workflows": True, "code": True, "openai_compat": True, "voice": True,
            "ecosystem": True, "activity": True, "neural": True, "data": True,
            "assistant": True, "handoff": True, "tools": True, "mcp": True,
            "context": True, "feedback": True, "catalog": True, "automation": True,
            "actions": True, "orchestrator": True, "codeexec": True, "graphics": True,
            "connectors": True, "safety": True,
        },
        "code_local_ready": bool(settings.ae_local_base_url),
        "openai_compatible": "/v1/chat/completions · /v1/embeddings · /v1/models",
    }


# Modules montés sur le gateway (auth par clé API)
app.include_router(provider_router, dependencies=[Depends(require_api_key)])
app.include_router(embeddings_router, dependencies=[Depends(require_api_key)])
app.include_router(rag_router, dependencies=[Depends(require_api_key)])
app.include_router(memory_router, dependencies=[Depends(require_api_key)])
app.include_router(knowledge_router, dependencies=[Depends(require_api_key)])
app.include_router(agent_router, dependencies=[Depends(require_api_key)])
app.include_router(workflow_router, dependencies=[Depends(require_api_key)])
app.include_router(code_router, dependencies=[Depends(require_api_key)])
app.include_router(voice_router, dependencies=[Depends(require_api_key)])
app.include_router(ecosystem_router, dependencies=[Depends(require_api_key)])
app.include_router(activity_router, dependencies=[Depends(require_api_key)])
app.include_router(neural_router, dependencies=[Depends(require_api_key)])
app.include_router(data_router, dependencies=[Depends(require_api_key)])
app.include_router(assistant_router, dependencies=[Depends(require_api_key)])
app.include_router(handoff_router, dependencies=[Depends(require_api_key)])
app.include_router(tools_router, dependencies=[Depends(require_api_key)])
app.include_router(mcp_router, dependencies=[Depends(require_api_key)])
app.include_router(context_router, dependencies=[Depends(require_api_key)])
app.include_router(feedback_router, dependencies=[Depends(require_api_key)])
app.include_router(catalog_router, dependencies=[Depends(require_api_key)])
app.include_router(automation_router, dependencies=[Depends(require_api_key)])
app.include_router(actions_router, dependencies=[Depends(require_api_key)])
app.include_router(orchestrator_router, dependencies=[Depends(require_api_key)])
app.include_router(codeexec_router, dependencies=[Depends(require_api_key)])
app.include_router(graphics_router, dependencies=[Depends(require_api_key)])
app.include_router(connectors_router, dependencies=[Depends(require_api_key)])
app.include_router(safety_router, dependencies=[Depends(require_api_key)])
# WebSocket (interface visuelle future) : auth par token de requête, hors dépendance d'en-tête.
app.include_router(assistant_ws_router)
# Endpoints compatibles OpenAI : auth Bearer OU X-API-Key (drop-in Open WebUI/LocalAI/…)
app.include_router(openai_router, dependencies=[Depends(require_bearer_or_key)])
