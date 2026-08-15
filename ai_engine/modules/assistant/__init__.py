"""Module assistant — assistant d'application scopé, intégrable à toutes les apps Lunziko.

Chaque application obtient un assistant **limité à sa zone de compétence** (dérivée du registre
écosystème, module `ecosystem`) : il assiste, corrige et agit dans ce périmètre, redirige hors
périmètre, et peut animer **jusqu'à 5 agents par application** pour fluidifier les tâches.
Fournit aussi une **connexion prête pour une future interface visuelle** (sessions + WebSocket +
contrat UI). Clean-room, aucune dépendance à Platform (identité/licences = consommées si besoin).
"""

MAX_AGENTS_PER_APP = 5
