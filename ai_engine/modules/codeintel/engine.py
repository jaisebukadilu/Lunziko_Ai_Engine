"""CodeIntelligence — indexation, recherche sémantique et compréhension de code.

Construit au-dessus de l'existant : embeddings + VectorPort (recherche sémantique, repli
hash hors-ligne), StoragePort (carte des fichiers), écosystème (contexte des 11 projets),
Code Execution Engine + Git via les outils. 100 % local.
"""

from __future__ import annotations

import re
from pathlib import Path

from ai_engine.core.registry import get_storage, get_vector
from ai_engine.modules.codeintel.languages import (
    detect_by_extension, families, language_count,
)
from ai_engine.modules.embeddings.manager import get_embedding_manager

# Répertoires ignorés lors de l'indexation (bruit / artefacts).
IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
               "target", ".next", ".turbo", "out", ".idea", ".vscode", "coverage",
               ".pytest_cache", ".mypy_cache", "Pods", ".gradle", "bin", "obj"}

MAX_FILE_BYTES = 400_000
MAX_FILES = 4000
CHUNK_LINES = 60

# Manifestes de dépendances par écosystème.
DEP_MANIFESTS = {
    "package.json": "npm", "requirements.txt": "pip", "pyproject.toml": "python",
    "Cargo.toml": "cargo", "go.mod": "go", "pom.xml": "maven", "build.gradle": "gradle",
    "build.gradle.kts": "gradle", "Package.swift": "spm", "pubspec.yaml": "pub",
    "Gemfile": "bundler", "composer.json": "composer",
}

# Extraction de symboles : motifs par grande famille syntaxique.
SYMBOL_PATTERNS = [
    ("function", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(")),           # python
    ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$]\w*)")),  # js/ts
    ("function", re.compile(r"^\s*func\s+([A-Za-z_]\w*)")),                            # go/swift
    ("function", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)")),                   # rust
    ("class", re.compile(r"^\s*(?:export\s+)?(?:public\s+|abstract\s+|final\s+)?class\s+([A-Za-z_]\w*)")),
    ("struct", re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)")),
    ("interface", re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_]\w*)")),
    ("type", re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_]\w*)\s*=")),
    ("enum", re.compile(r"^\s*(?:pub\s+|public\s+)?enum\s+([A-Za-z_]\w*)")),
]


class CodeIntelligence:
    def __init__(self) -> None:
        self._store = get_storage()
        self._vec = get_vector()
        self._emb = get_embedding_manager()

    @staticmethod
    def _ns(project: str) -> str:
        return f"codeindex:{project}"

    # --- Détection langage ----------------------------------------------
    def detect_language(self, path: str) -> dict | None:
        return detect_by_extension(path)

    def languages_meta(self) -> dict:
        return {"count": language_count(), "families": families()}

    # --- Parcours / architecture (sans indexation) ----------------------
    def _walk(self, root: Path):
        seen = 0
        for p in root.rglob("*"):
            if seen >= MAX_FILES:
                break
            if p.is_dir():
                continue
            if any(part in IGNORE_DIRS for part in p.parts):
                continue
            yield p
            seen += 1

    def understand(self, root_path: str) -> dict:
        """Résumé d'architecture : distribution des langages, fichiers clés, manifestes."""
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(root_path)
        by_lang: dict[str, int] = {}
        total = 0
        entrypoints: list[str] = []
        manifests: list[str] = []
        for p in self._walk(root):
            total += 1
            lang = detect_by_extension(p.name)
            key = lang["id"] if lang else "other"
            by_lang[key] = by_lang.get(key, 0) + 1
            if p.name in DEP_MANIFESTS:
                manifests.append(str(p.relative_to(root)))
            if p.name.lower() in ("main.py", "index.ts", "index.js", "main.go", "main.rs",
                                  "app.py", "main.swift", "program.cs", "__main__.py"):
                entrypoints.append(str(p.relative_to(root)))
        top = sorted(by_lang.items(), key=lambda kv: kv[1], reverse=True)
        return {
            "root": str(root),
            "files_scanned": total,
            "languages": dict(top),
            "primary_language": top[0][0] if top else None,
            "entrypoints": entrypoints[:20],
            "dependency_manifests": manifests[:20],
        }

    def dependencies(self, root_path: str) -> dict:
        """Extrait les dépendances déclarées des manifestes reconnus."""
        root = Path(root_path)
        out: dict[str, list[str]] = {}
        for p in self._walk(root):
            eco = DEP_MANIFESTS.get(p.name)
            if not eco:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_BYTES]
            except Exception:
                continue
            deps = self._parse_deps(p.name, text)
            if deps:
                out.setdefault(eco, [])
                out[eco].extend(deps)
        return {k: sorted(set(v))[:200] for k, v in out.items()}

    @staticmethod
    def _parse_deps(filename: str, text: str) -> list[str]:
        deps: list[str] = []
        if filename == "requirements.txt":
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    deps.append(re.split(r"[=<>!~ ]", line)[0])
        elif filename == "package.json":
            deps += re.findall(r'"([^"]+)"\s*:\s*"[^"]*"', text)
        elif filename in ("pyproject.toml", "Cargo.toml"):
            for m in re.finditer(r'^\s*([A-Za-z0-9_.\-]+)\s*=\s*[">{]', text, re.MULTILINE):
                deps.append(m.group(1))
        elif filename == "go.mod":
            deps += re.findall(r"^\s*([\w./\-]+)\s+v[\d.]", text, re.MULTILINE)
        return [d for d in deps if d and d not in ("dependencies", "devDependencies", "version", "name")]

    # --- Symboles --------------------------------------------------------
    def symbols(self, content: str, max_symbols: int = 200) -> list[dict]:
        out: list[dict] = []
        for i, line in enumerate(content.splitlines(), 1):
            for kind, pat in SYMBOL_PATTERNS:
                m = pat.match(line)
                if m:
                    out.append({"name": m.group(1), "kind": kind, "line": i})
                    break
            if len(out) >= max_symbols:
                break
        return out

    # --- Indexation sémantique ------------------------------------------
    async def index_repo(self, root_path: str, project: str) -> dict:
        root = Path(root_path)
        if not root.exists():
            raise FileNotFoundError(root_path)
        ns = self._ns(project)
        indexed = 0
        chunks = 0
        for p in self._walk(root):
            lang = detect_by_extension(p.name)
            if lang is None or lang["family"] in ("markup", "config", "style"):
                # on indexe surtout le code exécutable ; docs/config indexés par le RAG
                if lang is None:
                    continue
            try:
                if p.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            rel = str(p.relative_to(root))
            syms = self.symbols(text)
            self._store.put(ns, rel, {
                "path": rel, "language": lang["id"], "size": len(text),
                "symbols": [s["name"] for s in syms[:50]],
            })
            for idx, chunk in enumerate(self._chunk(text)):
                cid = f"{rel}#{idx}"
                vec = (await self._emb.embed([f"{lang['id']} {rel}\n{chunk}"])).vectors[0]
                self._vec.upsert(ns, cid, vec, {"path": rel, "language": lang["id"], "chunk": idx})
                chunks += 1
            indexed += 1
        meta = {"project": project, "root": str(root), "files_indexed": indexed, "chunks": chunks}
        self._store.put("codeindex_meta", project, meta)
        return meta

    @staticmethod
    def _chunk(text: str):
        lines = text.splitlines()
        for i in range(0, len(lines), CHUNK_LINES):
            block = "\n".join(lines[i:i + CHUNK_LINES]).strip()
            if block:
                yield block

    async def search_code(self, project: str, query: str, k: int = 8) -> list[dict]:
        ns = self._ns(project)
        qvec = (await self._emb.embed([query])).vectors[0]
        out = []
        for hit in self._vec.search(ns, qvec, k):
            out.append({
                "path": hit.get("meta", {}).get("path") or hit.get("path"),
                "language": hit.get("meta", {}).get("language"),
                "chunk": hit.get("meta", {}).get("chunk"),
                "score": round(hit["score"], 4),
                "id": hit["id"],
            })
        return out

    def indexed_projects(self) -> list[dict]:
        return self._store.list("codeindex_meta")

    # --- Contexte projet écosystème -------------------------------------
    def project_context(self, project: str) -> dict:
        """Croise avec le registre écosystème : ce que Code Intelligence sait d'un projet Lunziko."""
        try:
            from ai_engine.modules.ecosystem.engine import get_ecosystem_engine
            app = get_ecosystem_engine().get_app(project)
        except Exception:
            app = None
        meta = self._store.get("codeindex_meta", project)
        return {
            "project": project,
            "ecosystem_known": app is not None,
            "app": app,
            "index": meta,
            "note": "Code Intelligence connaît fonctionnalités, API, dépendances AI/Graphics, "
                    "Design System et contrats via le registre maître de l'écosystème.",
        }


def get_code_intelligence() -> CodeIntelligence:
    return CodeIntelligence()
