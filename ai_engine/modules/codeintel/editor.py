"""SafeEditor — écriture/modification contrôlée de fichiers (Code Intelligence).

Garde-fous (garantie « aucune action destructive sans filet ») :
  * SANDBOX DE CHEMIN : toute opération est confinée à un `root` (workspace) ; rejet du
    franchissement `..` et de tout chemin hors du root. Un `AE_CODEINTEL_WORKSPACE` optionnel
    fige un root autorisé global.
  * DRY-RUN par défaut : sans `confirm=True`, on renvoie un APERÇU (diff) sans rien écrire.
  * SAUVEGARDE RÉVERSIBLE : avant tout écrasement/suppression, le contenu original est
    sauvegardé (StoragePort) → `restore(backup_id)` rétablit.
  * ZONES PROTÉGÉES : refus d'écrire dans .git/, node_modules/, .venv/, secrets…
  * ÉDITION CIBLÉE : `edit` exige un `old_string` UNIQUE (comme un str-replace sûr).

Ne dépend d'aucun provider : opérations de fichiers pures + persistance des sauvegardes.
"""

from __future__ import annotations

import difflib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ai_engine.config import get_settings
from ai_engine.core.registry import get_storage

PROTECTED_PARTS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".ssh"}
PROTECTED_NAMES = {".env", "id_rsa", "id_ed25519", "credentials", ".pypirc", ".npmrc"}
BACKUP_NS = "codeintel_backups"
MAX_WRITE_BYTES = 2_000_000


class GuardrailError(RuntimeError):
    """Violation d'un garde-fou (chemin hors sandbox, zone protégée, écrasement non confirmé)."""


class SafeEditor:
    def __init__(self) -> None:
        self._store = get_storage()

    # --- Sandbox de chemin ----------------------------------------------
    def _resolve(self, root: str, rel: str) -> Path:
        pin = get_settings().ae_codeintel_workspace
        root_p = Path(root).resolve()
        if pin:
            pin_p = Path(pin).resolve()
            if not str(root_p).startswith(str(pin_p)):
                raise GuardrailError(f"root '{root}' hors du workspace autorisé '{pin}'")
        target = (root_p / rel).resolve()
        if root_p != target and not str(target).startswith(str(root_p) + __import__("os").sep):
            raise GuardrailError(f"chemin '{rel}' hors du workspace '{root}'")
        parts = set(target.parts)
        if parts & PROTECTED_PARTS or target.name in PROTECTED_NAMES:
            raise GuardrailError(f"zone protégée : {rel}")
        return target

    @staticmethod
    def _diff(before: str, after: str, path: str) -> str:
        return "".join(difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True),
            fromfile=f"a/{path}", tofile=f"b/{path}"))

    def _backup(self, root: str, rel: str, content: str) -> str:
        bid = uuid.uuid4().hex
        self._store.put(BACKUP_NS, bid, {
            "id": bid, "root": root, "rel": rel, "content": content,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        return bid

    # --- Écriture / création --------------------------------------------
    def write(self, root: str, rel: str, content: str, *,
              confirm: bool = False, allow_overwrite: bool = False) -> dict:
        if len(content.encode("utf-8", "replace")) > MAX_WRITE_BYTES:
            raise GuardrailError("contenu trop volumineux")
        target = self._resolve(root, rel)
        exists = target.exists()
        before = target.read_text(encoding="utf-8", errors="replace") if exists else ""
        if exists and not allow_overwrite:
            raise GuardrailError(f"{rel} existe déjà — passez allow_overwrite=True pour écraser")
        diff = self._diff(before, content, rel)
        if not confirm:
            return {"action": "write", "path": rel, "exists": exists, "confirmed": False,
                    "dry_run": True, "diff": diff}
        backup_id = self._backup(root, rel, before) if exists else None
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"action": "write", "path": rel, "written": True, "overwritten": exists,
                "backup_id": backup_id, "bytes": len(content)}

    # --- Édition ciblée (str-replace sûr) -------------------------------
    def edit(self, root: str, rel: str, old_string: str, new_string: str, *,
             confirm: bool = False) -> dict:
        target = self._resolve(root, rel)
        if not target.exists():
            raise GuardrailError(f"{rel} introuvable")
        before = target.read_text(encoding="utf-8", errors="replace")
        occurrences = before.count(old_string)
        if occurrences == 0:
            raise GuardrailError("old_string introuvable dans le fichier")
        if occurrences > 1:
            raise GuardrailError(f"old_string non unique ({occurrences} occurrences) — préciser le contexte")
        after = before.replace(old_string, new_string, 1)
        diff = self._diff(before, after, rel)
        if not confirm:
            return {"action": "edit", "path": rel, "confirmed": False, "dry_run": True, "diff": diff}
        backup_id = self._backup(root, rel, before)
        target.write_text(after, encoding="utf-8")
        return {"action": "edit", "path": rel, "edited": True, "backup_id": backup_id, "diff": diff}

    # --- Suppression SOFT (sauvegarde puis retrait) ---------------------
    def delete(self, root: str, rel: str, *, confirm: bool = False) -> dict:
        target = self._resolve(root, rel)
        if not target.exists():
            raise GuardrailError(f"{rel} introuvable")
        before = target.read_text(encoding="utf-8", errors="replace")
        if not confirm:
            return {"action": "delete", "path": rel, "confirmed": False, "dry_run": True,
                    "preview": before[:2000]}
        backup_id = self._backup(root, rel, before)
        target.unlink()
        return {"action": "delete", "path": rel, "deleted": True, "backup_id": backup_id,
                "note": "sauvegardé (réversible via restore)"}

    # --- Restauration ----------------------------------------------------
    def restore(self, backup_id: str) -> dict:
        rec = self._store.get(BACKUP_NS, backup_id)
        if not rec:
            raise GuardrailError("sauvegarde introuvable")
        target = self._resolve(rec["root"], rec["rel"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rec["content"], encoding="utf-8")
        return {"restored": rec["rel"], "backup_id": backup_id}

    def list_backups(self, root: str | None = None) -> list[dict]:
        rows = self._store.list(BACKUP_NS)
        if root:
            rp = str(Path(root).resolve())
            rows = [r for r in rows if str(Path(r["root"]).resolve()) == rp]
        out = [{"id": r["id"], "rel": r["rel"], "root": r["root"], "at": r["at"]} for r in rows]
        out.sort(key=lambda r: r["at"], reverse=True)
        return out


def get_safe_editor() -> SafeEditor:
    return SafeEditor()
