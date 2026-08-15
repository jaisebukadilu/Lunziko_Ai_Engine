"""Module graphics — branchement au Lunziko Graphics Engine (dépôt séparé, JSON-RPC).

Point d'intégration pour que les Brains multimédias (image/vision/video/3d/cad) délèguent le
rendu/traitement au Graphics Engine (22 agents : imaging/asset/vector/pdf/cad/bim/sketch…).
Adaptateur CLIENT : si `AE_GRAPHICS_ENGINE_URL` est vide, non branché (Brains restent déclarés).
Le Graphics Engine n'est PAS modifié — on consomme son contrat JSON-RPC versionné.
"""
