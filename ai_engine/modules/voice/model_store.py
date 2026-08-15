"""Magasin de modèles voix (« mémoire interne ») : catalogue + registre des packs.

V-0 : métadonnées (catalogue 18 langues, registre installé) + arborescence sous
<AI_ENGINE_HOME>/voice/. Téléchargement réel des poids : phase V-4.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from ai_engine.config import get_settings
from ai_engine.modules.voice.schemas import LanguagePack, PackQuality

_CATALOG_FILE = Path(__file__).resolve().parent / "data" / "language_catalog.json"


@lru_cache
def load_catalog() -> dict[str, dict]:
    raw = json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
    return {p["id"]: p for p in raw["packs"]}


class VoiceModelStore:
    """Accès au dossier <home>/voice et à son registry.json."""

    def __init__(self) -> None:
        self.home = get_settings().voice_home

    @property
    def packs_dir(self) -> Path:
        return self.home / "packs"

    @property
    def shared_dir(self) -> Path:
        return self.home / "shared"

    @property
    def registry_path(self) -> Path:
        return self.home / "registry.json"

    def ensure_dirs(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.packs_dir.mkdir(exist_ok=True)
        self.shared_dir.mkdir(exist_ok=True)
        if not self.registry_path.exists():
            self._write_registry({"version": 1, "installed": {}})

    def _read_registry(self) -> dict:
        if not self.registry_path.exists():
            return {"version": 1, "installed": {}}
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _write_registry(self, data: dict) -> None:
        self.registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def installed_ids(self) -> set[str]:
        return set(self._read_registry().get("installed", {}).keys())

    def register_pack(self, pack_id: str, version: str) -> None:
        reg = self._read_registry()
        reg.setdefault("installed", {})[pack_id] = {
            "version": version,
            "installed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_registry(reg)
        (self.packs_dir / pack_id).mkdir(exist_ok=True)

    def unregister_pack(self, pack_id: str) -> bool:
        reg = self._read_registry()
        if pack_id in reg.get("installed", {}):
            del reg["installed"][pack_id]
            self._write_registry(reg)
            return True
        return False

    def get_pack_meta(self, pack_id: str) -> dict | None:
        return load_catalog().get(pack_id)

    def list_packs(self) -> list[LanguagePack]:
        installed = self.installed_ids()
        reg = self._read_registry().get("installed", {})
        out: list[LanguagePack] = []
        for pid, p in load_catalog().items():
            out.append(
                LanguagePack(
                    id=pid,
                    name=p["name"],
                    installed=pid in installed,
                    version=reg.get(pid, {}).get("version"),
                    size_mb=p["size_mb"],
                    stt_model=p["stt_model"],
                    tts_model=p["tts_model"],
                    mt_engine=p["mt_engine"],
                    license=p["license"],
                    quality=PackQuality(**p["quality"]),
                )
            )
        return out

    def download_pack(self, pack_id: str) -> None:
        """Téléchargement des poids (Whisper/Kokoro/Piper/MADLAD) — phase V-4."""
        raise NotImplementedError("download_pack: prévu en phase V-4")


@lru_cache
def get_voice_store() -> VoiceModelStore:
    store = VoiceModelStore()
    store.ensure_dirs()
    return store
