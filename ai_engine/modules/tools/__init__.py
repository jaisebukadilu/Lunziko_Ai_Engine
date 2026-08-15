"""Module tools — tool-calling natif (A-4b) : les agents AGISSENT, pas seulement génèrent.

Registre d'outils (nom + description + schéma JSON + handler), outils intégrés branchés sur
les capacités existantes (écosystème, handoff, données, ML, activité), et une boucle
d'exécution provider-agnostique (le modèle demande un outil → on l'exécute → on reboucle).
"""
