"""Module codeexec — Code Execution Engine (A-11), sûr par défaut.

Niveau 0 : évaluateur d'expressions restreint (AST, liste blanche) — réellement sûr, toujours
disponible. Niveau 1 : sandbox subprocess isolé — DÉSACTIVÉ par défaut (opt-in), à n'activer
que sous isolation OS pour du code non fiable. Cf. ../CODE_EXECUTION_SANDBOX.md.
"""
