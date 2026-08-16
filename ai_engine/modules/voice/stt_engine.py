"""Moteur STT (V-1/V-2) — reconnaissance vocale via Whisper (faster-whisper / ctranslate2).

Chargement paresseux du modèle (`AE_STT_MODEL`, défaut `base`), téléchargé au premier usage.
Actif si le paquet `faster-whisper` est installé (extra `voice-stt`) — sinon l'endpoint reste 501.
Décodage audio multi-format (wav/mp3/…) via PyAV. 100 % local.
"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

from ai_engine.config import get_settings

_MODEL = None


def stt_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


def get_stt_model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel(get_settings().ae_stt_model, device="cpu", compute_type="int8")
    return _MODEL


def transcribe(audio_bytes: bytes, lang: str = "auto") -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="ae_stt_")) / "audio.bin"
    tmp.write_bytes(audio_bytes)
    try:
        model = get_stt_model()
        segments, info = model.transcribe(
            str(tmp), language=None if lang in ("", "auto") else lang, vad_filter=True)
        text = "".join(s.text for s in segments).strip()
        return {"text": text, "lang": info.language,
                "lang_probability": round(getattr(info, "language_probability", 0.0), 3),
                "duration_s": round(getattr(info, "duration", 0.0), 2),
                "model": get_settings().ae_stt_model}
    finally:
        try:
            tmp.unlink()
            tmp.parent.rmdir()
        except Exception:
            pass
