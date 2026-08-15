"""Parseur du registre maître Lunziko (REGISTRE_ECOSYSTEME_LUNZIKO.md).

Pur (aucune I/O, aucune dépendance externe) : prend le texte Markdown du registre et
retourne des entrées structurées par application. Robuste au format §1 (roster) : les
blocs `#### <App>` du §1.A (socle) et §1.B (métier) sont extraits ; §1.C (roadmap prose)
et §1.D (tableau) sont ignorés pour le roster mais restitués séparément.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

_H2 = re.compile(r"^##\s+(.*)$")
_H3 = re.compile(r"^###\s+(.*)$")
_H4 = re.compile(r"^####\s+(.*)$")
_ITALIC_PAREN = re.compile(r"\s*\*\(.*?\)\*\s*$")       # « *(suite ERP …)* » en fin de titre
_TRAIL_PAREN = re.compile(r"\s*\([^)]*\)\s*$")           # « (LGE) », « (Lunziko DociaPub) »
_FIELD = re.compile(r"^[-*]\s*\*\*(?P<label>[^:*]+?)\s*:\*\*\s*(?P<value>.*)$")
_BULLET = re.compile(r"^\s*[-*]\s+(?P<text>.*)$")
_VERSION = re.compile(r"\*\*Version\s*:\*\*\s*(?P<v>[^\n—-]+)", re.IGNORECASE)


@dataclass
class AppEntry:
    slug: str
    name: str
    section: str                 # "1.A" (socle/agrégateur) | "1.B" (métier)
    is_aggregator: bool
    category: str = ""
    status: str = ""
    functions: list[str] = field(default_factory=list)
    exposes: str = ""
    consumes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def searchable_text(self) -> str:
        parts = [self.name, self.category, self.status, *self.functions]
        if self.exposes:
            parts.append(f"Expose : {self.exposes}")
        if self.consumes:
            parts.append(f"Consomme : {self.consumes}")
        return "\n".join(p for p in parts if p)


def slugify(name: str) -> str:
    """« Lunziko AI Engine » -> « ai-engine » ; « DociaPub » -> « dociapub »."""
    s = name.strip().lower()
    s = _TRAIL_PAREN.sub("", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if s.startswith("lunziko-"):
        s = s[len("lunziko-"):]
    return s or "app"


def _clean_name(raw: str) -> str:
    name = _ITALIC_PAREN.sub("", raw).strip()
    name = _TRAIL_PAREN.sub("", name).strip()
    return name


def _split_expose_consume(value: str) -> tuple[str, str]:
    """« expose … **Consomme :** … » -> (expose, consomme)."""
    m = re.search(r"\*\*Consomme\s*:\*\*", value)
    if not m:
        return _strip_md(value), ""
    exposes = value[: m.start()]
    consumes = value[m.end():]
    return _strip_md(exposes), _strip_md(consumes)


def _strip_md(text: str) -> str:
    text = re.sub(r"\*\*|\*|`", "", text)
    return re.sub(r"\s+", " ", text).strip(" .;—-")


def parse_registry(markdown: str) -> dict:
    """Retourne {version, apps: [AppEntry.to_dict…], sections}."""
    lines = markdown.splitlines()

    version = ""
    mv = _VERSION.search(markdown)
    if mv:
        version = mv.group("v").strip()

    apps: list[AppEntry] = []
    current_section = ""          # "1.A" / "1.B" / "1.C" / "1.D" …
    in_roster = False             # dans « ## 1. Roster … »
    app: AppEntry | None = None
    field_ctx = ""                # dernier label rencontré (pour rattacher les sous-bullets)

    def close_app() -> None:
        nonlocal app
        if app is not None:
            apps.append(app)
            app = None

    for line in lines:
        h2 = _H2.match(line)
        if h2:
            close_app()
            in_roster = h2.group(1).strip().startswith("1.")
            current_section = ""
            continue

        if not in_roster:
            continue

        h3 = _H3.match(line)
        if h3:
            close_app()
            m = re.match(r"^(1\.[A-D])", h3.group(1).strip())
            current_section = m.group(1) if m else ""
            continue

        # On ne construit le roster que pour §1.A (socle) et §1.B (métier).
        h4 = _H4.match(line)
        if h4 and current_section in ("1.A", "1.B"):
            close_app()
            name = _clean_name(h4.group(1))
            app = AppEntry(
                slug=slugify(name),
                name=name,
                section=current_section,
                is_aggregator=(current_section == "1.A"),
            )
            field_ctx = ""
            continue

        if app is None:
            continue

        # Champ de premier niveau (bullet à la colonne 0 : « - **Label :** valeur »).
        fld = _FIELD.match(line)
        if fld:
            label = fld.group("label").strip().lower()
            value = fld.group("value").strip()
            field_ctx = label
            if label.startswith("catégorie"):
                app.category = _strip_md(value)
            elif label.startswith("statut"):
                app.status = _strip_md(value)
            elif label.startswith("fonction"):
                # en-tête de la liste de fonctions ; les sous-bullets suivent
                if value:
                    app.functions.append(_strip_md(value))
            elif label.startswith("expose"):
                app.exposes, app.consumes = _split_expose_consume(value)
            continue

        # Sous-puce indentée : c'est une fonction quand on est sous « Fonctions … ».
        sub = _BULLET.match(line)
        if sub and field_ctx.startswith("fonction"):
            txt = _strip_md(sub.group("text"))
            if txt:
                app.functions.append(txt)
            continue

    close_app()

    return {
        "version": version,
        "count": len(apps),
        "apps": [a.to_dict() for a in apps],
    }
