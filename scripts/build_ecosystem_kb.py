#!/usr/bin/env python3
"""Génère docs/ECOSYSTEME_LUNZIKO.md à partir du registre maître Lunziko.

La base de connaissance écosystème de CE projet s'ALIMENTE du fichier maître
`REGISTRE_ECOSYSTEME_LUNZIKO.md` (racine Lunziko). Ne pas éditer la sortie à la
main : relancer ce script (règle §0.4 « analyse au lancement »).

Usage:
    python build_ecosystem_kb.py --project "Lunziko Graphics Engine" \
        [--registry <chemin>] [--out <chemin>]

Résolution du registre (1er trouvé) : --registry, env LUNZIKO_REGISTRY_PATH,
env AE_REGISTRY_PATH, puis candidats relatifs remontant vers la racine Lunziko,
puis le chemin absolu par défaut.
"""
from __future__ import annotations
import argparse, os, re, sys, datetime
from pathlib import Path

DEFAULT_ABS = r"C:\Users\Joe\Desktop\Lunziko\REGISTRE_ECOSYSTEME_LUNZIKO.md"
FNAME = "REGISTRE_ECOSYSTEME_LUNZIKO.md"


def resolve_registry(cli: str | None) -> Path | None:
    cands: list[str] = []
    if cli:
        cands.append(cli)
    for env in ("LUNZIKO_REGISTRY_PATH", "AE_REGISTRY_PATH"):
        if os.environ.get(env):
            cands.append(os.environ[env])
    # remonte l'arborescence depuis ce script pour trouver le fichier racine
    here = Path(__file__).resolve()
    for parent in here.parents:
        cands.append(str(parent / FNAME))
    cands.append(DEFAULT_ABS)
    for c in cands:
        p = Path(c)
        if p.is_file():
            return p
    return None


def _section(text: str, start_pat: str, stop_pats: tuple[str, ...]) -> str:
    """Extrait le bloc démarrant à la 1re ligne matchant start_pat jusqu'à la
    prochaine ligne matchant l'un des stop_pats (exclue)."""
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for ln in lines:
        if not capturing:
            if re.match(start_pat, ln):
                capturing = True
                out.append(ln)
            continue
        if any(re.match(sp, ln) for sp in stop_pats):
            break
        out.append(ln)
    return "\n".join(out).strip()


def parse_apps(text: str) -> list[dict]:
    """Retourne la liste des blocs d'app (#### <nom>) du roster §1."""
    lines = text.splitlines()
    apps: list[dict] = []
    cur: dict | None = None
    for ln in lines:
        m = re.match(r"^####\s+(.+?)\s*(?:\*\(|$)", ln)
        if m:
            if cur:
                apps.append(cur)
            name = re.sub(r"\s*\*\(.*$", "", m.group(1)).strip()
            cur = {"name": name, "body": []}
            continue
        if cur is not None:
            # fin de roster : on s'arrête aux titres de niveau <= ###
            if re.match(r"^###?\s", ln) and not re.match(r"^####", ln):
                apps.append(cur)
                cur = None
                continue
            if re.match(r"^---\s*$", ln):
                apps.append(cur)
                cur = None
                continue
            cur["body"].append(ln)
    if cur:
        apps.append(cur)
    # nettoie & extrait catégorie + expose/consomme
    for a in apps:
        body = "\n".join(a["body"]).strip()
        a["body"] = body
        cat = re.search(r"\*\*Catégorie\s*:\*\*\s*(.+)", body)
        a["categorie"] = cat.group(1).strip() if cat else ""
        exp = re.search(r"\*\*Expose\s*:\*\*\s*(.+)", body)
        a["expose"] = exp.group(1).strip() if exp else ""
    return apps


def build(project: str, registry: Path) -> str:
    text = registry.read_text(encoding="utf-8")
    ver = re.search(r"^>\s*\*\*Version\s*:\*\*\s*(.+)$", text, re.M)
    version = ver.group(1).strip() if ver else "inconnue"
    now = datetime.date.today().isoformat()

    apps = parse_apps(text)
    gov = _section(text, r"^##\s+0\.", (r"^##\s+\d", r"^---\s*$"))
    matrix = _section(text, r"^##\s+2\.", (r"^##\s+\d", r"^---\s*$"))
    suites = _section(text, r"^###\s+1\.D", (r"^##\s+\d", r"^---\s*$"))

    # bloc du projet courant (rôle)
    me = next((a for a in apps if a["name"].lower() == project.lower()), None)

    out: list[str] = []
    out.append(f"# Base de connaissance — Écosystème Lunziko (vue {project})")
    out.append("")
    out.append("> ⚙️ **FICHIER AUTO-GÉNÉRÉ — NE PAS ÉDITER À LA MAIN.**")
    out.append(f"> Alimenté depuis le registre maître : `{registry}`")
    out.append(f"> Version du registre : **{version}** · généré le {now}.")
    out.append("> Régénérer : `python scripts/build_ecosystem_kb.py --project "
               f"\"{project}\"` (règle §0.4 : à chaque lancement).")
    out.append("")
    if me:
        out.append(f"## Rôle de {project} (extrait du registre)")
        out.append("")
        out.append(me["body"])
        out.append("")
    out.append("## Toutes les applications de l'écosystème (roster §1)")
    out.append("")
    out.append("| Application | Catégorie | Expose (résumé) |")
    out.append("|---|---|---|")
    for a in apps:
        cat = a["categorie"].replace("|", "／")
        exp = a["expose"].split("**Consomme")[0].replace("|", "／").strip(" .")
        marker = " ⭐" if me and a is me else ""
        out.append(f"| **{a['name']}**{marker} | {cat} | {exp} |")
    out.append("")
    out.append("## Détail des fonctions par application (extrait du registre)")
    out.append("")
    for a in apps:
        out.append(f"### {a['name']}")
        out.append("")
        out.append(a["body"])
        out.append("")
    if suites:
        out.append("## Suites et applications (§1.D)")
        out.append("")
        out.append(suites)
        out.append("")
    if gov:
        out.append("## Règles de gouvernance (§0)")
        out.append("")
        out.append(gov)
        out.append("")
    if matrix:
        out.append("## Matrice de communication obligatoire (§2)")
        out.append("")
        out.append(matrix)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--registry", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    reg = resolve_registry(args.registry)
    if not reg:
        print("ERREUR: registre introuvable (REGISTRE_ECOSYSTEME_LUNZIKO.md).",
              file=sys.stderr)
        return 2
    content = build(args.project, reg)
    out = args.out or str(Path(__file__).resolve().parent.parent / "docs" /
                          "ECOSYSTEME_LUNZIKO.md")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(content, encoding="utf-8")
    print(f"OK -> {out} ({len(content.splitlines())} lignes, "
          f"registre v.{re.search(r'Version.*', content).group(0)[:40] if False else ''})")
    print(f"     source: {reg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
