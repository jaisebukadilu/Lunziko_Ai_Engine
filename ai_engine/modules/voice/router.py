"""Routeur du module voix — monté par le gateway sous /v1/voice.

Consolide voices · packs · tts · stt · translate · speak.
Inférence (tts/stt/translate/speak) : validation réelle + 501 jusqu'aux phases V-1→V-3.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

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


# --- Profils de rendu + voix personnalisées/fine-tunées (V-5) ------------
@router.get("/profiles")
def voice_profiles() -> list[dict]:
    from ai_engine.modules.voice.profiles import all_profiles
    return all_profiles()


@router.get("/profiles/{voice_id}")
def voice_profile(voice_id: str) -> dict:
    from ai_engine.modules.voice.profiles import render_profile
    prof = render_profile(voice_id)
    if not prof.get("known"):
        raise HTTPException(status_code=404, detail=f"Voix inconnue: {voice_id}")
    return prof


class CustomVoiceRequest(BaseModel):
    lang: str
    model_path: str
    quality: str = "alpha"


@router.get("/custom-voices")
def list_custom_voices(lang: str | None = None) -> list[dict]:
    from ai_engine.modules.voice.profiles import get_custom_voice_store
    return get_custom_voice_store().list(lang)


@router.post("/voices/{voice_id}/model")
def register_custom_voice(voice_id: str, req: CustomVoiceRequest) -> dict:
    """Enregistre une voix fine-tunée (ex. lingála/swahili) : un .onnx local pour (voice_id, lang)."""
    from ai_engine.modules.voice.profiles import get_custom_voice_store
    try:
        return get_custom_voice_store().register(voice_id, req.lang, req.model_path,
                                                 quality=req.quality)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/voices/{voice_id}/model")
def unregister_custom_voice(voice_id: str, lang: str) -> dict:
    from ai_engine.modules.voice.profiles import get_custom_voice_store
    if not get_custom_voice_store().unregister(voice_id, lang):
        raise HTTPException(status_code=404, detail="voix personnalisée non enregistrée")
    return {"voice_id": voice_id, "lang": lang, "status": "removed"}


# --- Préparation de fine-tuning (V-5) -----------------------------------
class FinetunePrepareRequest(BaseModel):
    pairs: list[dict] = Field(min_length=1, description="paires {audio, text}")
    lang: str
    voice_id: str
    task: str = "tts"


@router.post("/finetune/prepare")
def finetune_prepare(req: FinetunePrepareRequest) -> dict:
    from ai_engine.modules.voice.finetune import prepare_dataset
    try:
        return prepare_dataset(req.pairs, lang=req.lang, voice_id=req.voice_id, task=req.task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/finetune/datasets")
def finetune_datasets() -> list[dict]:
    from ai_engine.modules.voice.finetune import list_datasets
    return list_datasets()


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


def _parse_components(components: str | None) -> tuple[str, ...]:
    from ai_engine.modules.voice.pack_downloader import ALL_COMPONENTS, DEFAULT_COMPONENTS
    if not components:
        return DEFAULT_COMPONENTS
    wanted = tuple(c.strip() for c in components.split(",") if c.strip())
    bad = [c for c in wanted if c not in ALL_COMPONENTS]
    if bad:
        raise HTTPException(status_code=400, detail=f"Composants inconnus: {bad} (attendu: {ALL_COMPONENTS})")
    return wanted


@router.get("/packs/{pack_id}/plan")
def plan_pack(pack_id: str, components: str | None = None) -> dict:
    """Dry-run : ce qui serait téléchargé pour ce pack, sans rien récupérer."""
    from ai_engine.modules.voice.pack_downloader import plan_pack as _plan
    try:
        return _plan(pack_id, components=_parse_components(components))
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pack inconnu: {pack_id}")


@router.post("/packs/{pack_id}/install", status_code=202)
def install_pack(pack_id: str, components: str | None = None, dry_run: bool = False) -> dict:
    """Télécharge (réellement, V-4) les composants du pack : `components=stt,tts[,mt]`.

    STT/MT sont partagés multilingues ; TTS est la voix Piper propre à la langue.
    Chaque composant n'est récupéré que si l'extra correspondant est installé.
    """
    from ai_engine.modules.voice.pack_downloader import install_pack as _install
    try:
        return _install(pack_id, components=_parse_components(components), dry_run=dry_run)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pack inconnu: {pack_id}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"install: {e}")


@router.delete("/packs/{pack_id}")
def uninstall_pack(pack_id: str) -> dict:
    if not get_voice_store().unregister_pack(pack_id):
        raise HTTPException(status_code=404, detail=f"Pack non installé: {pack_id}")
    return {"id": pack_id, "status": "removed"}


# --- Inférence (V-1 → V-3) ----------------------------------------------
@router.post("/tts")
def tts(req: TTSRequest):
    if req.voice not in VOICE_IDS:
        raise HTTPException(status_code=400, detail=f"Voix inconnue: {req.voice}")
    from ai_engine.modules.voice.tts_engine import synthesize, tts_available
    if not tts_available():
        raise HTTPException(status_code=501,
                            detail="TTS: installer l'extra `voice-tts` (piper-tts) + une voix .onnx")
    try:
        wav, model = synthesize(req.text, lang=req.lang or "auto", voice_id=req.voice)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS: {e}")
    return Response(content=wav, media_type="audio/wav",
                    headers={"X-Voice-Model": model, "X-Voice-Id": req.voice,
                             "X-Audio-Bytes": str(len(wav))})


@router.get("/tts/status")
def tts_status() -> dict:
    from ai_engine.modules.voice.tts_engine import list_voice_models, tts_available, voices_dir
    return {"available": tts_available(), "voices_dir": str(voices_dir()),
            "voices": list_voice_models(), "engine": "piper"}


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
async def translate(req: TranslateRequest) -> dict:
    # V-3 : MADLAD-400 on-device ; fallback via le Provider Manager PROPRE à l'AI Engine.
    from ai_engine.modules.voice.translate_engine import get_translation_engine
    try:
        return await get_translation_engine().translate(req.text, req.source, req.target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MT: {e}")


@router.get("/translate/status")
def translate_status() -> dict:
    from ai_engine.modules.voice.translate_engine import (
        LANG_NAMES, madlad_available, resolve_backend,
    )
    from ai_engine.config import get_settings
    return {
        "backend": resolve_backend(),
        "madlad_available": madlad_available(),
        "madlad_model": get_settings().ae_mt_model,
        "languages": sorted(LANG_NAMES),
        "llm_fallback": True,
    }


@router.post("/speak")
async def speak(
    audio: UploadFile = File(...),
    target: str = Form(...),
    voice: str = Form(...),
    source: str = Form("auto"),
    format: str = Form("wav"),
):
    """Interprète en un appel : STT → MT → TTS (audio d'entrée → audio traduit)."""
    if voice not in VOICE_IDS:
        raise HTTPException(status_code=400, detail=f"Voix inconnue: {voice}")

    from ai_engine.modules.voice.stt_engine import stt_available, transcribe
    from ai_engine.modules.voice.translate_engine import get_translation_engine
    from ai_engine.modules.voice.tts_engine import synthesize, tts_available

    if not stt_available():
        raise HTTPException(status_code=501, detail="speak: STT indisponible (extra `voice-stt`)")
    if not tts_available():
        raise HTTPException(status_code=501, detail="speak: TTS indisponible (extra `voice-tts`)")

    # 1) STT : audio → texte source
    data = await audio.read()
    try:
        stt_res = transcribe(data, lang=source)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"speak/STT: {e}")
    src_text = stt_res.get("text", "")
    detected = stt_res.get("lang", source)
    if not src_text:
        raise HTTPException(status_code=422, detail="speak: aucune parole détectée dans l'audio")

    # 2) MT : texte source → texte cible
    try:
        mt = await get_translation_engine().translate(src_text, source=source, target=target)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"speak/MT: {e}")
    tgt_text = mt["text"]

    # 3) TTS : texte cible → audio
    try:
        wav, model = synthesize(tgt_text, lang=target)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"speak/TTS: {e}")

    return Response(
        content=wav, media_type="audio/wav",
        headers={
            "X-Source-Lang": str(detected),
            "X-Source-Text": src_text[:512],
            "X-Target-Lang": target,
            "X-Target-Text": tgt_text[:512],
            "X-MT-Backend": mt["backend"],
            "X-Voice-Model": model,
        },
    )
