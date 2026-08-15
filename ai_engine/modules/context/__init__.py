"""Module context — Couche de Contexte Unifié (A-14→A-16).

Rassemble en temps réel le contexte utile à l'IA d'application : profil & habitudes (A-14),
état applicatif live éphémère (A-16), et un assembleur (A-15) qui unifie profil + habitudes +
activité + état live + connaissance + écosystème, sous budget, pour l'agent. Offline, sur les
ports existants. Frontière : identité/RBAC = Platform (consommée), jamais recodée ici.
"""
