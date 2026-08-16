"""Routeur du module voix — monté par le gateway sous /v1/voice.

Consolide voices · packs · tts · stt · translate · speak.
Inférence (tts/stt/translate/speak) : validation réelle + 501 jusqu'aux phases V-1→V-3.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ai_engine.modules.voice.model_store import get_voice_store
from ai_engine.modules.voice.schemas import LanguagePack, TranslateRequest, TTSRequest, Voice
from ai_engine.modules.voice.voices import CANONICAL_VOICES, VOICE_IDS, get_voice

router = APIRouter(prefix="/v1/voice", tags=["voice"])


# --- Voix ----------------------------------------------------------------
@router.get("/voices", response_model=list[Voice])
def list_voices() -> list[Voice]:
    return CANONICAL_VOICES


@router.get("/voices/{voice_id}", response_model=Voice)
def get_one_voice(voice_id: str) -> Voice:
    v = get_voice(voice_id)
    if v is None:
        raise HTTPException(status_code=404, detail=f"Voix inconnue: {voice_id}")
    return v


# --- Packs de langues ----------------------------------------------------
@router.get("/packs", response_model=list[LanguagePack])
def list_packs() -> list[LanguagePack]:
    return get_voice_store().list_packs()


@router.get("/packs/{pack_id}", response_model=LanguagePack)
def get_pack(pack_id: str) -> LanguagePack:
    packs = {p.id: p for p in get_voice_store().list_packs()}
    if pack_id not in packs:
        raise HTTPException(status_code=404, detail=f"Pack inconnu: {pack_id}")
    return packs[pack_id]


@router.post("/packs/{pack_id}/install", status_code=202)
def install_pack(pack_id: str) -> dict:
    store = get_voice_store()
    if store.get_pack_meta(pack_id) is None:
        raise HTTPException(status_code=404, detail=f"Pack inconnu: {pack_id}")
    version = "0.1.0"
    store.register_pack(pack_id, version)
    return {
        "id": pack_id,
        "status": "registered",
        "version": version,
        "note": "Métadonnées enregistrées. Téléchargement des modèles: phase V-4.",
    }


@router.delete("/packs/{pack_id}")
def uninstall_pack(pack_id: str) -> dict:
    if not get_voice_store().unregister_pack(pack_id):
        raise HTTPException(status_code=404, detail=f"Pack non installé: {pack_id}")
    return {"id": pack_id, "status": "removed"}


# --- Inférence (V-1 → V-3) ----------------------------------------------
@router.post("/tts")
def tts(req: TTSRequest) -> dict:
    if req.voice not in VOICE_IDS:
        raise HTTPException(status_code=400, detail=f"Voix inconnue: {req.voice}")
    if req.lang not in get_voice_store().installed_ids():
        raise HTTPException(
            status_code=409,
            detail=f"Pack '{req.lang}' non installé. POST /v1/voice/packs/{req.lang}/install d'abord.",
        )
    raise HTTPException(status_code=501, detail="TTS: inférence prévue en phase V-1")


@router.post("/stt")
async def stt(audio: UploadFile = File(...), lang: str = Form("auto")) -> dict:
    if audio.content_type and not audio.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Fichier audio attendu")
    from ai_engine.modules.voice.stt_engine import stt_available, transcribe
    if not stt_available():
        raise HTTPException(status_code=501,
                            detail="STT: installer l'extra `voice-stt` (faster-whisper)")
    data = await audio.read()
    try:
        return transcribe(data, lang=lang)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"STT: {e}")


@router.get("/stt/status")
def stt_status() -> dict:
    from ai_engine.modules.voice.stt_engine import stt_available
    from ai_engine.config import get_settings
    return {"available": stt_available(), "model": get_settings().ae_stt_model, "engine": "faster-whisper"}


@router.post("/translate")
def translate(req: TranslateRequest) -> dict:
    if req.source == req.target:
        raise HTTPException(status_code=400, detail="source et target identiques")
    # V-3 : MADLAD-400 ; fallback via le Provider Manager PROPRE à l'AI Engine
    raise HTTPException(status_code=501, detail="MT: inférence prévue en phase V-3")


@router.post("/speak")
async def speak(
    audio: UploadFile = File(...),
    target: str = Form(...),
    voice: str = Form(...),
    source: str = Form("auto"),
    format: str = Form("mp3"),
) -> dict:
    if voice not in VOICE_IDS:
        raise HTTPException(status_code=400, detail=f"Voix inconnue: {voice}")
    raise HTTPException(status_code=501, detail="speak: pipeline assemblé en phase V-3")
