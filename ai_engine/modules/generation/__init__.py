"""Génération multimédia (image/vidéo/audio/3D) — activation des Brains génératifs.

Dispatche vers un backend génératif branché (Graphics Engine, ComfyUI, API hébergée,
diffusers local GPU). Sans backend disponible : réponse `deferred` explicite indiquant le
backend/GPU requis et les modèles candidats (Model Registry) — jamais de génération simulée.
"""
