"""Module actions — Action Registry : les apps déclarent leurs actions exécutables.

Chaque application publie les actions qu'elle sait exécuter (créer un événement, modifier une
ligne, envoyer un message…) avec un schéma d'arguments. L'AI Engine les découvre, valide une
invocation et produit une **instruction d'action structurée** — l'exécution réelle revient à
l'app hôte (jamais à l'AI Engine). Complète handoff (navigation/fichiers) et tools (capacités IA).
"""
