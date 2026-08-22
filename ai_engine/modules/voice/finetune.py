"""Préparation de fine-tuning voix (V-5) — datasets TTS/STT pour lingála/swahili & voix enfants.

L'ENTRAÎNEMENT lui-même (Piper/VITS pour TTS, Whisper pour STT) nécessite GPU + corpus et se
fait hors bac à sable. Ce module prépare des **datasets propres et versionnés** à partir de
paires (audio, transcription) : nettoyage du texte (module `data`), validation, écriture d'un
**manifeste d'entraînement** dans `<home>/voice/finetune/<lang>/<voice_id>/`.

Format de manifeste = JSONL `{audio, text}` (compatible pipelines Piper/VITS/Whisper courants).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ai_engine.config import get_settings


def _dataset_dir(lang: str, voice_id: str) -> Path:
    return get_settings().voice_home / "finetune" / lang / voice_id


def _norm(s: str) -> str:
    return " ".join(str(s).split()).strip()


def prepare_dataset(
    pairs: list[dict], *, lang: str, voice_id: str, task: str = "tts", min_len: int = 1,
) -> dict:
    """Prépare un dataset de fine-tuning à partir de paires {audio, text}.

    - normalise les transcriptions (espaces), applique une longueur mini, déduplique ;
    - écarte les paires sans audio ou sans texte valide ;
    - écrit `manifest.jsonl` + `meta.json`.
    """
    if task not in ("tts", "stt"):
        raise ValueError("task doit être 'tts' ou 'stt'")

    valid: list[dict] = []
    dropped = 0
    seen: set[str] = set()
    for p in pairs:
        text = _norm(p.get("text", ""))
        audio = _norm(p.get("audio", ""))
        if not audio or len(text) < min_len or text in seen:
            dropped += 1
            continue
        seen.add(text)
        valid.append({"audio": audio, "text": text})

    out_dir = _dataset_dir(lang, voice_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as f:
        for row in valid:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = {
        "lang": lang, "voice_id": voice_id, "task": task,
        "pairs_in": len(pairs), "pairs_kept": len(valid), "dropped": dropped,
        "manifest": str(manifest),
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "next_step": ("Entraîner hors ligne (GPU) : TTS=Piper/VITS, STT=fine-tune Whisper ; "
                      "puis enregistrer le .onnx via /v1/voice/voices/{voice_id}/model."),
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    return meta


def list_datasets() -> list[dict]:
    root = get_settings().voice_home / "finetune"
    if not root.is_dir():
        return []
    out = []
    for meta_file in root.rglob("meta.json"):
        try:
            out.append(json.loads(meta_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out
