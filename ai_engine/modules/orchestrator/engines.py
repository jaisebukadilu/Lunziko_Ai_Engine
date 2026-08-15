"""Engine Registry — catalogue des moteurs de LAIA (mappe les modules existants).

Chaque « Engine » LAIA pointe vers un module déjà livré (aucune duplication). Statut `active`
si le module existe, `planned` sinon (Code Execution, Search web, Image/Video/3D generation…).
"""

from __future__ import annotations


def _e(eid, name, mission, module, status="active"):
    return {"id": eid, "name": name, "mission": mission, "module": module, "status": status}


# Mapping Engine LAIA -> module existant de l'AI Engine.
ENGINES = [
    _e("orchestrator", "AI Orchestrator Engine", "Chef d'orchestre", "orchestrator"),
    _e("inference", "Inference Engine", "Exécution des modèles (cloud/local/natif)", "provider+neural.inference"),
    _e("rag", "RAG Engine", "Recherche augmentée", "rag"),
    _e("search", "Search Engine", "Recherche locale (web = planned)", "rag+ecosystem"),
    _e("memory", "Memory Engine", "Mémoire chiffrée", "memory"),
    _e("knowledge", "Knowledge Engine", "Connaissances & graphes", "knowledge"),
    _e("context", "Context Engine", "Contexte unifié temps réel", "context"),
    _e("reasoning", "Reasoning Engine", "Planification/raisonnement", "agent+orchestrator"),
    _e("agent", "Agent Engine", "Agents autonomes", "agents"),
    _e("tool", "Tool Engine", "Outils/function calling", "tools+actions"),
    _e("workflow", "Workflow Engine", "Pipelines composables", "workflows"),
    _e("automation", "Automation Engine", "Flux de nœuds", "automation"),
    _e("data", "Data Engine", "Données & ML", "data+neural.ml"),
    _e("neural", "Neural Engine", "Backends + routeur d'intention", "neural"),
    _e("voice", "Voice Engine", "STT/TTS/dialogue (V-1 à venir)", "voice", status="partial"),
    _e("validation", "Validation Engine", "Vérification des résultats", "orchestrator.validation"),
    _e("mcp", "MCP Engine", "Interop Model Context Protocol", "mcp"),
    _e("code_execution", "Code Execution Engine", "Exécution sandboxée (safe-eval ON, subprocess opt-in)", "codeexec", status="partial"),
    _e("graphics", "Graphics Bridge Engine", "Pont REST vers le Lunziko Graphics Engine (93 endpoints)", "graphics", status="partial"),
    # Déclarés (à brancher plus tard).
    _e("image_generation", "Image Generation Engine", "Génération/édition d'image", "graphics-engine", status="planned"),
    _e("video", "Video Engine", "Pipeline vidéo", "graphics-engine", status="planned"),
    _e("audio", "Audio Engine", "Pipeline audio", "—", status="planned"),
    _e("3d", "3D Intelligence Engine", "Pipeline 3D", "graphics-engine", status="planned"),
    _e("ui_generation", "UI Generation Engine", "Génération d'interfaces", "code+design-system", status="planned"),
    _e("evaluation", "Evaluation Engine", "Benchmark/qualité", "—", status="planned"),
    _e("safety", "Safety Engine", "Garde-fous", "—", status="planned"),
]

_BY_ID = {e["id"]: e for e in ENGINES}


def list_engines(status: str | None = None) -> list[dict]:
    engines = ENGINES if status is None else [e for e in ENGINES if e["status"] == status]
    return sorted(engines, key=lambda e: (e["status"] != "active", e["id"]))


def get_engine(eid: str) -> dict | None:
    return _BY_ID.get(eid)
