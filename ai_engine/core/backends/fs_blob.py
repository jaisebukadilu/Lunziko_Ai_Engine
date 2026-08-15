"""BlobPort — stockage d'objets sur le filesystem local (défaut standalone)."""

from __future__ import annotations

import hashlib
from pathlib import Path


class FsBlob:
    def __init__(self, base_dir: Path) -> None:
        self._dir = base_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _safe(self, key: str) -> Path:
        # clé -> nom de fichier sûr (hash pour éviter la traversée de chemin)
        name = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._dir / name

    def write(self, key: str, data: bytes) -> str:
        p = self._safe(key)
        p.write_bytes(data)
        return str(p)

    def read(self, key: str) -> bytes | None:
        p = self._safe(key)
        return p.read_bytes() if p.exists() else None

    def delete(self, key: str) -> bool:
        p = self._safe(key)
        if p.exists():
            p.unlink()
            return True
        return False
