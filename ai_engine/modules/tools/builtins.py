"""Outils intégrés — exposent les capacités de l'AI Engine comme fonctions appelables.

Tous exécutables hors-ligne (repli hash) et sûrs (lecture/analyse ; le handoff produit une
instruction, il n'exécute rien sur le système). Ajouter un outil = 1 spec + 1 handler.
"""

from __future__ import annotations

from ai_engine.modules.provider.base import ToolSpec


async def _ecosystem_search(args: dict) -> object:
    from ai_engine.modules.ecosystem.engine import get_ecosystem_engine

    hits = await get_ecosystem_engine().search(args["query"], int(args.get("k", 3)))
    return [{"slug": h["slug"], "name": h.get("name"), "score": h["score"]} for h in hits]


async def _handoff_open_with(args: dict) -> object:
    from ai_engine.modules.handoff.engine import get_handoff_engine

    return await get_handoff_engine().open_with(args["from_app"], args["filename"])


async def _data_clean_text(args: dict) -> object:
    from ai_engine.modules.data.cleaner import clean_texts

    return clean_texts(list(args["texts"]), min_len=int(args.get("min_len", 1)))["report"]


async def _ml_predict(args: dict) -> object:
    from ai_engine.modules.neural.ml import get_ml_trainer

    return await get_ml_trainer().predict(args["name"], args["text"])


async def _activity_timeline(args: dict) -> object:
    from ai_engine.modules.activity.engine import get_activity_engine

    return get_activity_engine().timeline(args["user_id"], limit=int(args.get("limit", 5)))


async def _web_search(args: dict) -> object:
    from ai_engine.modules.search.engine import get_search_engine

    res = await get_search_engine().search(args["query"], k=int(args.get("k", 5)))
    return res.get("results", res)


async def _code_detect_language(args: dict) -> object:
    from ai_engine.modules.codeintel.engine import get_code_intelligence

    return get_code_intelligence().detect_language(args["path"]) or {"language": None}


async def _code_understand(args: dict) -> object:
    from ai_engine.modules.codeintel.engine import get_code_intelligence

    return get_code_intelligence().understand(args["root"])


async def _code_search(args: dict) -> object:
    from ai_engine.modules.codeintel.engine import get_code_intelligence

    return await get_code_intelligence().search_code(
        args["project"], args["query"], k=int(args.get("k", 8)))


async def _code_dependencies(args: dict) -> object:
    from ai_engine.modules.codeintel.engine import get_code_intelligence

    return get_code_intelligence().dependencies(args["root"])


async def _code_project_context(args: dict) -> object:
    from ai_engine.modules.codeintel.engine import get_code_intelligence

    return get_code_intelligence().project_context(args["project"])


_BUILTINS = [
    (ToolSpec(
        name="ecosystem_search",
        description="Trouve les applications Lunziko compétentes pour une tâche ou un sujet.",
        parameters={"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer", "default": 3}},
            "required": ["query"]}),
     _ecosystem_search),
    (ToolSpec(
        name="handoff_open_with",
        description="Détermine dans quelle app Lunziko ouvrir un fichier (par type de fichier).",
        parameters={"type": "object", "properties": {
            "from_app": {"type": "string"}, "filename": {"type": "string"}},
            "required": ["from_app", "filename"]}),
     _handoff_open_with),
    (ToolSpec(
        name="data_clean_text",
        description="Nettoie/déduplique un corpus texte et renvoie un rapport.",
        parameters={"type": "object", "properties": {
            "texts": {"type": "array", "items": {"type": "string"}},
            "min_len": {"type": "integer", "default": 1}},
            "required": ["texts"]}),
     _data_clean_text),
    (ToolSpec(
        name="ml_predict",
        description="Classe un texte avec un modèle ML entraîné (par son nom).",
        parameters={"type": "object", "properties": {
            "name": {"type": "string"}, "text": {"type": "string"}},
            "required": ["name", "text"]}),
     _ml_predict),
    (ToolSpec(
        name="activity_timeline",
        description="Renvoie les dernières actions d'un utilisateur.",
        parameters={"type": "object", "properties": {
            "user_id": {"type": "string"}, "limit": {"type": "integer", "default": 5}},
            "required": ["user_id"]}),
     _activity_timeline),
    (ToolSpec(
        name="web_search",
        description="Recherche sur le web (résultats titre/url/extrait) pour le Research Brain.",
        parameters={"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer", "default": 5}},
            "required": ["query"]}),
     _web_search),
    # --- Code Intelligence (utilisable depuis VS Code/Cursor/PowerShell via MCP + tool-calling) ---
    (ToolSpec(
        name="code_detect_language",
        description="Détecte le langage de programmation d'un fichier par son chemin.",
        parameters={"type": "object", "properties": {"path": {"type": "string"}},
                    "required": ["path"]}),
     _code_detect_language),
    (ToolSpec(
        name="code_understand",
        description="Analyse l'architecture d'un dépôt (langages, points d'entrée, manifestes).",
        parameters={"type": "object", "properties": {"root": {"type": "string"}},
                    "required": ["root"]}),
     _code_understand),
    (ToolSpec(
        name="code_search",
        description="Recherche sémantique dans le code indexé d'un projet.",
        parameters={"type": "object", "properties": {
            "project": {"type": "string"}, "query": {"type": "string"},
            "k": {"type": "integer", "default": 8}},
            "required": ["project", "query"]}),
     _code_search),
    (ToolSpec(
        name="code_dependencies",
        description="Extrait les dépendances déclarées d'un dépôt (npm/pip/cargo/go/maven…).",
        parameters={"type": "object", "properties": {"root": {"type": "string"}},
                    "required": ["root"]}),
     _code_dependencies),
    (ToolSpec(
        name="code_project_context",
        description="Contexte écosystème d'un projet Lunziko (fonctions, API, contrats, index).",
        parameters={"type": "object", "properties": {"project": {"type": "string"}},
                    "required": ["project"]}),
     _code_project_context),
]


def register_builtins(registry) -> None:
    for spec, handler in _BUILTINS:
        registry.register(spec, handler)
