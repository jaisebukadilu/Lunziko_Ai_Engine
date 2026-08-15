"""Module automation (A-10) — moteur d'automatisation par nœuds (clean-room, inspiré n8n).

Un flux = une suite de nœuds ; chaque nœud appelle un outil du registre (A-4b) avec des
arguments pouvant référencer l'entrée du flux ou la sortie d'un nœud précédent (`$input.x`,
`$node_id.champ`). Flux et exécutions persistés. Concept inspiré de n8n (fair-code) mais
réimplémenté FROM SCRATCH — aucun code copié.
"""
