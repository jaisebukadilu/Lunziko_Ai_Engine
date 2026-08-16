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


def synthesize(text: str, lang: str = "auto") -> tuple[bytes, str]:
    """Retourne (wav_bytes, voice_model_name)."""
    model = _pick_model(lang)
    if model is None:
        raise RuntimeError("aucune voix Piper (.onnx) disponible ; "
                           "télécharger via `python -m piper.download_voices <voix>`")
    voice = _load(model)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        voice.synthesize_wav(text, wf)
    return buf.getvalue(), model.stem
