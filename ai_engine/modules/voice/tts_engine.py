"""Moteur TTS (V-1) — synthèse vocale via Piper (ONNX, 100 % local).

Actif si le paquet `piper-tts` est installé (extra `voice-tts`) ET au moins une voix `.onnx`
est présente dans le dossier des voix (`AE_TTS_VOICES_DIR`, défaut `<home>/voice/piper`).
Sélection de la voix par langue (nom de fichier) sinon voix par défaut. Renvoie du WAV.
"""

from __future__ import annotations

import importlib.util
import io
import wave
from pathlib import Path

from ai_engine.config import get_settings

_CACHE: dict[str, object] = {}


def tts_available() -> bool:
    return importlib.util.find_spec("piper") is not None


def voices_dir() -> Path:
    s = get_settings()
    return Path(s.ae_tts_voices_dir) if s.ae_tts_voices_dir else (s.voice_home / "piper")


def list_voice_models() -> list[str]:
    d = voices_dir()
    return sorted(p.stem for p in d.glob("*.onnx")) if d.is_dir() else []


def _pick_model(lang: str) -> Path | None:
    d = voices_dir()
    if not d.is_dir():
        return None
    onnx = sorted(d.glob("*.onnx"))
    if not onnx:
        return None
    s = get_settings()
    if s.ae_tts_default_voice:
        cand = d / f"{s.ae_tts_default_voice}.onnx"
        if cand.exists():
            return cand
    if lang and lang not in ("", "auto"):
        for p in onnx:  # ex : "fr" -> "fr_FR-siwis-medium"
            if p.stem.lower().startswith(lang.lower()):
                return p
    return onnx[0]


def _load(model: Path):
    key = str(model)
    if key not in _CACHE:
        from piper import PiperVoice
        _CACHE[key] = PiperVoice.load(str(model), str(model) + ".json")
    return _CACHE[key]


def _resolve_model(lang: str, voice_id: str | None) -> Path | None:
    """Résout le modèle .onnx : voix fine-tunée (voice_id+lang) sinon base par langue."""
    if voice_id:
        from ai_engine.modules.voice.profiles import get_custom_voice_store
        custom = get_custom_voice_store().resolve(voice_id, lang)
        if custom:
            return Path(custom)
    return _pick_model(lang)


def synthesize(text: str, lang: str = "auto", voice_id: str | None = None) -> tuple[bytes, str]:
    """Retourne (wav_bytes, voice_model_name).

    Si `voice_id` (une des 10 voix Lunziko) est fourni : privilégie une voix fine-tunée
    enregistrée pour (voice_id, lang), et applique le profil de rendu (débit) de la voix.
    """
    model = _resolve_model(lang, voice_id)
    if model is None:
        raise RuntimeError("aucune voix Piper (.onnx) disponible ; "
                           "télécharger via `python -m piper.download_voices <voix>` "
                           "ou enregistrer une voix fine-tunée")
    voice = _load(model)
    syn_config = None
    if voice_id:
        from ai_engine.modules.voice.profiles import render_profile
        prof = render_profile(voice_id)
        if prof.get("known") and prof.get("length_scale") is not None:
            try:
                from piper import SynthesisConfig
                syn_config = SynthesisConfig(length_scale=prof["length_scale"])
            except Exception:
                syn_config = None  # API Piper variable : repli débit par défaut
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        if syn_config is not None:
            try:
                voice.synthesize_wav(text, wf, syn_config=syn_config)
            except TypeError:
                voice.synthesize_wav(text, wf)  # version Piper sans syn_config
        else:
            voice.synthesize_wav(text, wf)
    return buf.getvalue(), model.stem
