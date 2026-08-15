"""Taxonomie d'intention partagée : exemples (neuronal) + racines lexicales (mots-clés).

Source unique pour les deux routeurs. Les racines sont **normalisées sans accent** et
matchées en **préfixe de token** → tolèrent conjugaisons/pluriels/accents
(« résume/résumé/résumer/résumons », « mémo », « analyse/analyser/analytique »).
"""

from __future__ import annotations

import re
import unicodedata

INTENTS = ["document", "research", "data", "crm", "creative", "general"]

# Exemples d'entraînement du routeur neuronal (variés, incluant des formulations difficiles).
INTENT_EXAMPLES: dict[str, list[str]] = {
    "document": [
        "résume ce document en quelques points",
        "corrige les fautes d'orthographe de ce texte",
        "rédige un rapport clair et structuré",
        "reformule ce paragraphe plus simplement",
        "fais une synthèse du compte rendu",
        "peux-tu condenser ce long mémo en trois lignes",
        "prépare une note de synthèse soignée",
        "relis et améliore le style de cette lettre",
        "mets ce brouillon au propre",
        "récapitule les points essentiels du procès-verbal",
    ],
    "research": [
        "trouve des informations sur ce sujet",
        "recherche les sources qui parlent de cela",
        "cherche ce que dit la documentation",
        "quelles références existent sur cette question",
        "je veux enquêter sur ce point",
        "je souhaite investiguer ce que disent les publications",
        "renseigne-toi sur l'état de l'art",
        "explore la littérature disponible",
        "documente-toi et cite tes sources",
        "quelles études existent à ce propos",
    ],
    "data": [
        "analyse ces chiffres et donne les tendances",
        "calcule la moyenne de ces statistiques",
        "quels sont les indicateurs clés de ces données",
        "fais une analyse quantitative du tableau",
        "compare ces mesures numériques",
        "donne-moi les moyennes et écarts-types de ce jeu",
        "quel est le total et le pourcentage de progression",
        "sors les KPI de ce fichier",
        "quelle corrélation entre ces variables",
        "agrège ces montants par mois",
    ],
    "crm": [
        "ajoute un nouveau contact client",
        "quel est le suivi de ce prospect",
        "gère la relation avec ce membre",
        "mets à jour la fiche de ce client",
        "prépare le prochain rendez-vous commercial",
        "planifie un point de suivi avec ce prospect",
        "où en est cette opportunité de vente",
        "relance ce lead resté sans réponse",
        "note les coordonnées de ce nouveau contact",
        "qui est le commercial en charge de ce compte",
    ],
    "creative": [
        "génère des idées originales pour ce projet",
        "imagine un concept créatif",
        "propose un brainstorming de noms",
        "crée un design innovant",
        "invente une accroche marketing",
        "propose des concepts inédits pour la campagne",
        "trouve un slogan percutant",
        "imagine des pistes originales pour le logo",
        "donne-moi des idées de nom de marque",
        "conçois une identité visuelle audacieuse",
    ],
    "general": [
        "bonjour, peux-tu m'aider",
        "explique-moi comment ça marche",
        "j'ai une question générale",
        "que peux-tu faire pour moi",
        "donne-moi ton avis",
        "salut, j'ai besoin d'un coup de main",
        "peux-tu m'expliquer ce point",
        "merci, une dernière chose",
        "quelle est ta recommandation",
        "aide-moi à comprendre",
    ],
}

# Racines lexicales (préfixes normalisés sans accent). Distinctes par intention.
KEYWORD_ROOTS: dict[str, list[str]] = {
    "document": ["resum", "synth", "redig", "corrig", "reformul", "relis", "relir",
                 "paragraph", "rapport", "texte", "memo", "note", "condens", "recap",
                 "brouillon", "orthograph", "redact", "compte rendu", "proces-verbal"],
    "research": ["cherch", "trouv", "recherch", "source", "referenc", "enquet",
                 "investig", "renseign", "explor", "fouill", "etude", "publicat",
                 "litterature", "etat de l'art"],
    "data": ["analys", "calcul", "statist", "chiffr", "donnee", "moyenne", "ecart",
             "tendanc", "indicateur", "kpi", "metric", "mesur", "quantitat", "graph",
             "tableau", "somme", "total", "pourcent", "correl", "agreg", "variable"],
    "crm": ["client", "prospect", "contact", "vente", "commercial", "crm", "membre",
            "rendez", "suivi", "relation", "fiche", "lead", "opportunit", "relanc", "compte"],
    "creative": ["cre", "gener", "imagin", "idee", "brainstorm", "design", "concept",
                 "innov", "invent", "accroch", "slogan", "logo", "marque", "identite visuel"],
    "general": ["bonjour", "salut", "aide", "aider", "explique", "expliqu", "comment",
                "question", "avis", "recommand", "comprend", "coup de main"],
}


def normalize(text: str) -> str:
    """Minuscule + suppression des accents (NFKD)."""
    s = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def keyword_scores(query: str) -> dict[str, float]:
    """Score lexical par intention : nombre de racines distinctes présentes."""
    norm = normalize(query)
    tokens = re.findall(r"[a-z0-9']+", norm)
    scores = {intent: 0.0 for intent in INTENTS}
    for intent, roots in KEYWORD_ROOTS.items():
        for root in roots:
            if " " in root:                      # expression multi-mots
                if root in norm:
                    scores[intent] += 1.0
                continue
            if any(t.startswith(root) or (len(root) >= 5 and root in t) for t in tokens):
                scores[intent] += 1.0
    return scores


def keyword_best(query: str) -> tuple[str, float]:
    """Meilleure intention lexicale (+ score). 'general' si aucun signal."""
    scores = keyword_scores(query)
    best = max(scores, key=scores.get)
    return (best, scores[best]) if scores[best] > 0 else ("general", 0.0)
