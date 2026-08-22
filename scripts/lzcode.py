#!/usr/bin/env python3
"""lzcode — CLI Lunziko Code Intelligence (utilisable depuis PowerShell, terminal, Xcode, CI).

Client HTTP léger du gateway AI Engine. Aucune dépendance hors stdlib (urllib).

Exemples :
  python lzcode.py detect src/App.tsx
  python lzcode.py understand .
  python lzcode.py deps .
  python lzcode.py index . --project mon-projet
  python lzcode.py search mon-projet "où est la facturation"
  python lzcode.py languages
  python lzcode.py project lunziko-bi

Config par variables d'environnement :
  AE_URL      (défaut http://127.0.0.1:8770)
  AE_API_KEY  (si le gateway exige une clé — en-tête X-API-Key)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("AE_URL", "http://127.0.0.1:8770")
KEY = os.environ.get("AE_API_KEY", "")


def _req(method: str, path: str, *, params: dict | None = None, body: dict | None = None):
    url = BASE.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if KEY:
        req.add_header("X-API-Key", KEY)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode(errors="replace")[:500]}
    except urllib.error.URLError as e:
        return {"error": "connexion", "detail": f"{e} — le gateway AI Engine est-il lancé sur {BASE} ?"}


def main() -> int:
    ap = argparse.ArgumentParser(prog="lzcode", description="Lunziko Code Intelligence CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("detect"); p.add_argument("path")
    p = sub.add_parser("understand"); p.add_argument("root")
    p = sub.add_parser("deps"); p.add_argument("root")
    p = sub.add_parser("index"); p.add_argument("root"); p.add_argument("--project", required=True)
    p = sub.add_parser("search"); p.add_argument("project"); p.add_argument("query"); p.add_argument("-k", type=int, default=8)
    sub.add_parser("languages")
    sub.add_parser("projects")
    p = sub.add_parser("project"); p.add_argument("name")

    a = ap.parse_args()
    if a.cmd == "detect":
        out = _req("GET", "/v1/code-intelligence/detect", params={"path": a.path})
    elif a.cmd == "understand":
        out = _req("GET", "/v1/code-intelligence/understand", params={"root": a.root})
    elif a.cmd == "deps":
        out = _req("GET", "/v1/code-intelligence/dependencies", params={"root": a.root})
    elif a.cmd == "index":
        out = _req("POST", "/v1/code-intelligence/index", body={"root": a.root, "project": a.project})
    elif a.cmd == "search":
        out = _req("POST", "/v1/code-intelligence/search",
                   body={"project": a.project, "query": a.query, "k": a.k})
    elif a.cmd == "languages":
        out = _req("GET", "/v1/code-intelligence/languages")
        out = out.get("meta", out)  # résumé (le catalogue complet est volumineux)
    elif a.cmd == "projects":
        out = _req("GET", "/v1/code-intelligence/projects")
    elif a.cmd == "project":
        out = _req("GET", f"/v1/code-intelligence/project/{a.name}")
    else:
        ap.print_help(); return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if not (isinstance(out, dict) and out.get("error")) else 1


if __name__ == "__main__":
    sys.exit(main())
