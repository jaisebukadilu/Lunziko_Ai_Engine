"""Téléchargement réel des packs de langues (V-4).

Un « pack » = tout le nécessaire pour une langue. Les composants lourds MULTILINGUES
(Whisper STT, MADLAD MT) sont PARTAGÉS (`shared/`, téléchargés une fois) ; seul le
spécifique langue (voix Piper TTS) est propre au pack.

Chaque composant n'est téléchargé que si l'extra correspondant est installé
(`voice-stt` / `voice-tts` / `voice-mt`) — sinon il est reporté proprement, sans échec.
Aucun téléchargement n'est déclenché à l'import : tout passe par `install_pack`.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from ai_engine.config import get_settings
from ai_engine.modules.voice.model_store import get_voice_store, load_catalog, load_shared

# MADLAD-400 (3B) pèse plusieurs Go : téléchargé seulement sur demande explicite.
DEFAULT_COMPONENTS = ("stt", "tts")
ALL_COMPONENTS = ("stt", "tts", "mt")


def _have(pkg: str) -> bool:
    return importlib.util.find_spec(pkg) is not None


def _tts_voices_dir() -> Path:
    from ai_engine.modules.voice.tts_engine import voices_dir
    return voices_dir()


# --- Téléchargements par composant --------------------------------------
def download_tts_voice(voice_id: str, dry_run: bool = False) -> dict:
    """Télécharge une voix Piper (.onnx + .json) dans le dossier des voix."""
    d = _tts_voices_dir()
    onnx = d / f"{voice_id}.onnx"
    if onnx.exists():
        return {"status": "present", "voice": voice_id, "path": str(onnx)}
    if not _have("piper"):
        return {"status": "skipped", "reason": "extra `voice-tts` (piper-tts) non installé", "voice": voice_id}
    if dry_run:
        return {"status": "planned", "voice": voice_id, "path": str(onnx)}
    d.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [sys.executable, "-m", "piper.download_voices", voice_id, "--data-dir", str(d)],
            check=True, capture_output=True, timeout=1800,
        )
    except subprocess.CalledProcessError as e:
        return {"status": "error", "voice": voice_id,
                "detail": (e.stderr or b"").decode(errors="replace")[:400]}
    except Exception as e:  # timeout, réseau…
        return {"status": "error", "voice": voice_id, "detail": str(e)[:400]}
    return {"status": "installed" if onnx.exists() else "error", "voice": voice_id, "path": str(onnx)}


def download_stt_model(whisper_model: str, dry_run: bool = False) -> dict:
    """Assure la présence du modèle Whisper partagé (téléchargé/caché par faster-whisper)."""
    if not _have("faster_whisper"):
        return {"status": "skipped", "reason": "extra `voice-stt` (faster-whisper) non installé",
                "model": whisper_model}
    if dry_run:
        return {"status": "planned", "model": whisper_model, "shared": True}
    try:
        from faster_whisper import WhisperModel
        WhisperModel(whisper_model, device="cpu", compute_type="int8")  # déclenche le download+cache
    except Exception as e:
        return {"status": "error", "model": whisper_model, "detail": str(e)[:400]}
    return {"status": "installed", "model": whisper_model, "shared": True}


def download_mt_model(mt_model: str, dry_run: bool = False) -> dict:
    """Assure la présence de MADLAD-400 partagé (lourd — sur demande explicite)."""
    if not _have("transformers"):
        return {"status": "skipped", "reason": "extra `voice-mt` (transformers) non installé",
                "model": mt_model}
    if dry_run:
        return {"status": "planned", "model": mt_model, "shared": True}
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        AutoTokenizer.from_pretrained(mt_model)
        AutoModelForSeq2SeqLM.from_pretrained(mt_model)
    except Exception as e:
        return {"status": "error", "model": mt_model, "detail": str(e)[:400]}
    return {"status": "installed", "model": mt_model, "shared": True}


# --- Orchestration d'un pack --------------------------------------------
def plan_pack(pack_id: str, components: tuple[str, ...] = DEFAULT_COMPONENTS) -> dict:
    """Simule l'installation (dry-run) : ce qui serait téléchargé, sans rien récupérer."""
    return install_pack(pack_id, components=components, dry_run=True)


def install_pack(
    pack_id: str,
    components: tuple[str, ...] = DEFAULT_COMPONENTS,
    dry_run: bool = False,
) -> dict:
    """Télécharge les composants demandés d'un pack et met à jour le registre.

    Retourne un rapport par composant. `dry_run=True` n'effectue aucun téléchargement.
    """
    meta = load_catalog().get(pack_id)
    if meta is None:
        raise KeyError(pack_id)
    shared = load_shared()
    report: dict[str, dict] = {}

    if "stt" in components:
        report["stt"] = download_stt_model(
            meta.get("stt_whisper") or shared.get("stt_whisper", "large-v3"), dry_run)

    if "tts" in components:
        voice = meta.get("tts_voice")
        if not voice:
            report["tts"] = {"status": "unavailable",
                             "reason": f"aucune voix Piper OSS pour '{pack_id}' (TTS {meta['quality']['tts']})"}
        else:
            report["tts"] = download_tts_voice(voice, dry_run)

    if "mt" in components:
        report["mt"] = download_mt_model(
            meta.get("mt_model") or shared.get("mt_model", "google/madlad400-3b-mt"), dry_run)

    ok = all(r.get("status") in ("installed", "present", "unavailable", "planned")
             for r in report.values())

    if not dry_run and ok:
        get_voice_store().register_pack(pack_id, version="1.0.0", components=report)

    return {
        "id": pack_id,
        "dry_run": dry_run,
        "requested": list(components),
        "components": report,
        "installed": (not dry_run) and ok,
    }
