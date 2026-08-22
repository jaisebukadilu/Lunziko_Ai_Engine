"""Catalogue des stratégies de raisonnement (inspiration OSS, réimplémentation clean-room).

Chaque entrée décrit une technique publique de raisonnement, sa source d'inspiration et son
cas d'usage. Les implémentations vivent dans `engine.py` — aucune ligne de code tierce copiée.
"""

from __future__ import annotations

STRATEGIES: list[dict] = [
    {
        "id": "chain_of_thought", "name": "Chain-of-Thought (CoT)",
        "inspiration": "Wei et al. 2022 — « Let's think step by step »",
        "description": "Raisonnement explicite étape par étape avant la réponse finale.",
        "best_for": ["arithmétique", "logique simple", "questions structurées"],
        "cost": "1 appel",
    },
    {
        "id": "self_consistency", "name": "Self-Consistency",
        "inspiration": "Wang et al. 2022 — échantillonnage + vote majoritaire",
        "description": "Génère plusieurs chaînes de raisonnement et retient la réponse majoritaire.",
        "best_for": ["math", "problèmes à réponse unique", "réduction de variance"],
        "cost": "N appels",
    },
    {
        "id": "tree_of_thoughts", "name": "Tree-of-Thoughts (ToT)",
        "inspiration": "Yao et al. 2023 — exploration/évaluation de branches",
        "description": "Explore plusieurs approches candidates, les évalue, développe la meilleure.",
        "best_for": ["planification", "problèmes ouverts", "recherche de solution"],
        "cost": "breadth+évaluation appels",
    },
    {
        "id": "reflexion", "name": "Reflexion (auto-critique)",
        "inspiration": "Shinn et al. 2023 — critique de soi puis révision",
        "description": "Produit une réponse, la critique, puis la révise pour l'améliorer.",
        "best_for": ["rédaction", "code", "réponses à corriger"],
        "cost": "3 appels",
    },
    {
        "id": "plan_and_solve", "name": "Plan-and-Solve",
        "inspiration": "Wang et al. 2023 — planifier puis exécuter",
        "description": "Établit d'abord un plan, puis résout en le suivant.",
        "best_for": ["tâches multi-étapes", "problèmes complexes"],
        "cost": "2 appels",
    },
    {
        "id": "least_to_most", "name": "Least-to-Most",
        "inspiration": "Zhou et al. 2022 — décomposition ordonnée",
        "description": "Décompose en sous-problèmes ordonnés, résolus du plus simple au plus complexe.",
        "best_for": ["généralisation compositionnelle", "problèmes imbriqués"],
        "cost": "décomposition + N appels",
    },
    {
        "id": "step_back", "name": "Step-Back Prompting",
        "inspiration": "Zheng et al. 2023 — abstraction du principe avant les détails",
        "description": "Dégage d'abord le principe/concept général, puis l'applique au cas précis.",
        "best_for": ["science", "raisonnement conceptuel"],
        "cost": "2 appels",
    },
    {
        "id": "react", "name": "ReAct (Raisonnement + Action)",
        "inspiration": "Yao et al. 2022 — alternance réflexion/action/observation",
        "description": "Alterne pensée et actions d'outils jusqu'à résolution (voir module `autonomy`).",
        "best_for": ["tâches outillées", "recherche", "agents"],
        "cost": "boucle multi-appels",
    },
    {
        "id": "debate", "name": "Multi-Agent Debate",
        "inspiration": "Du et al. 2023 — confrontation d'avis entre agents",
        "description": "Plusieurs raisonneurs débattent et convergent (voir Brain-to-Brain LAIA).",
        "best_for": ["questions controversées", "vérification croisée"],
        "cost": "agents × tours",
    },
]

_BY_ID = {s["id"]: s for s in STRATEGIES}


def all_strategies() -> list[dict]:
    return STRATEGIES


def get_strategy(sid: str) -> dict | None:
    return _BY_ID.get(sid)
