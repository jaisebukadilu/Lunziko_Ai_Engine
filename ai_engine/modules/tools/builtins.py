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
]


def register_builtins(registry) -> None:
    for spec, handler in _BUILTINS:
        registry.register(spec, handler)
