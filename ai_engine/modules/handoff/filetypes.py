"""Correspondance type de fichier → application Lunziko la plus adaptée (clean-room).

Table déterministe extension → (app, module, raison) + alternatives. Sert à proposer
l'ouverture/le transfert d'un fichier vers l'app compétente. Complétée si besoin par une
recherche sémantique dans le registre écosystème.
"""

from __future__ import annotations

import os

# ext -> (app_slug, module, raison, [alternatives app_slug])
_MAP: dict[str, tuple[str, str, str, list[str]]] = {}


def _reg(exts: str, app: str, module: str, why: str, alts: list[str] | None = None) -> None:
    for e in exts.split():
        _MAP[e] = (app, module, why, alts or [])


# Documents bureautiques -> DociaPub
_reg("doc docx odt rtf txt md", "dociapub", "MyWord", "traitement de texte")
_reg("xls xlsx ods csv tsv", "dociapub", "MySheet", "tableur", ["bi"])
_reg("ppt pptx odp", "dociapub", "MySlides", "présentations")
# PDF -> VidiaPub (édition) / DociaPub
_reg("pdf", "vidiapub", "PDF", "édition/manipulation PDF", ["dociapub"])
# Images -> VidiaPub Photo
_reg("png jpg jpeg gif webp tiff tif bmp heic", "vidiapub", "Photo", "retouche d'image")
_reg("svg", "vidiapub", "Publisher", "graphisme vectoriel / PAO", ["cad"])
# Design / PAO -> VidiaPub Publisher
_reg("psd ai indd afdesign afpub", "vidiapub", "Publisher", "PAO / mise en page")
# Vidéo / Audio -> VidiaPub
_reg("mp4 mov avi mkv webm", "vidiapub", "Vidéo", "montage vidéo")
_reg("mp3 wav flac aac ogg m4a", "vidiapub", "Audio", "édition audio")
# CAO / 3D -> Lunziko CAD (+ Graphics Engine)
_reg("dwg dxf step stp iges igs", "cad", "CAO", "conception 2D/3D paramétrique", ["graphics-engine"])
_reg("stl obj fbx gltf glb 3mf", "cad", "CAO", "modèle 3D", ["graphics-engine"])
_reg("ifc", "cad", "BIM", "maquette BIM", ["graphics-engine"])
# Données / analytique -> BI
_reg("json parquet db sqlite", "bi", "MyData/BI", "données structurées & analytique", ["dociapub"])


def resolve_extension(filename: str) -> dict | None:
    """Retourne l'app suggérée pour un fichier d'après son extension, ou None."""
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    if not ext or ext not in _MAP:
        return None
    app, module, why, alts = _MAP[ext]
    return {"extension": ext, "app": app, "module": module, "reason": why, "alternatives": alts}


def known_extensions() -> dict:
    """Catalogue ext -> app (pour information / UI)."""
    return {e: {"app": v[0], "module": v[1]} for e, v in sorted(_MAP.items())}
