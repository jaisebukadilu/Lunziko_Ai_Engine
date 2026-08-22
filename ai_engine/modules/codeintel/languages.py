"""Catalogue des langages de programmation — « connaître et maîtriser tous les langages ».

Data-driven et extensible : chaque entrée = famille, paradigmes, extensions, écosystème/cibles.
La détection par extension couvre aussi les langages hors de cette liste (fallback gracieux).
Couvre les langages généralistes, systèmes, web, mobile, data/ML, fonctionnels, scientifiques,
shells, requêtes, balisage/config, matériels (HDL) et historiques.
"""

from __future__ import annotations

# id, name, family, paradigms, exts[], targets/ecosystem
LANGUAGES: list[dict] = [
    # --- Généralistes / applicatifs ---
    {"id": "python", "name": "Python", "family": "general", "paradigms": ["oo", "imperative", "functional"], "exts": [".py", ".pyw", ".pyi"], "targets": ["backend", "data", "ml", "scripting"]},
    {"id": "javascript", "name": "JavaScript", "family": "web", "paradigms": ["oo", "functional", "event"], "exts": [".js", ".mjs", ".cjs"], "targets": ["web", "backend", "node"]},
    {"id": "typescript", "name": "TypeScript", "family": "web", "paradigms": ["oo", "functional", "typed"], "exts": [".ts", ".tsx", ".mts", ".cts"], "targets": ["web", "backend", "node"]},
    {"id": "java", "name": "Java", "family": "jvm", "paradigms": ["oo", "imperative"], "exts": [".java"], "targets": ["backend", "android", "enterprise"]},
    {"id": "kotlin", "name": "Kotlin", "family": "jvm", "paradigms": ["oo", "functional"], "exts": [".kt", ".kts"], "targets": ["android", "backend", "multiplatform"]},
    {"id": "csharp", "name": "C#", "family": "dotnet", "paradigms": ["oo", "functional"], "exts": [".cs"], "targets": ["backend", "windows", "unity", "wpf", "winui"]},
    {"id": "fsharp", "name": "F#", "family": "dotnet", "paradigms": ["functional", "oo"], "exts": [".fs", ".fsi", ".fsx"], "targets": ["dotnet", "data"]},
    {"id": "vbnet", "name": "Visual Basic .NET", "family": "dotnet", "paradigms": ["oo", "imperative"], "exts": [".vb"], "targets": ["windows", "office"]},
    {"id": "go", "name": "Go", "family": "systems", "paradigms": ["imperative", "concurrent"], "exts": [".go"], "targets": ["backend", "cloud", "cli"]},
    {"id": "rust", "name": "Rust", "family": "systems", "paradigms": ["systems", "functional", "safe"], "exts": [".rs"], "targets": ["systems", "wasm", "tauri", "cli"]},
    {"id": "cpp", "name": "C++", "family": "systems", "paradigms": ["oo", "generic", "systems"], "exts": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"], "targets": ["systems", "games", "graphics", "hpc"]},
    {"id": "c", "name": "C", "family": "systems", "paradigms": ["imperative", "systems"], "exts": [".c", ".h"], "targets": ["systems", "embedded", "kernel"]},
    {"id": "objc", "name": "Objective-C", "family": "apple", "paradigms": ["oo"], "exts": [".m", ".mm"], "targets": ["macos", "ios"]},
    {"id": "swift", "name": "Swift", "family": "apple", "paradigms": ["oo", "functional", "protocol"], "exts": [".swift"], "targets": ["macos", "ios", "visionos", "swiftui", "server"]},
    {"id": "dart", "name": "Dart", "family": "general", "paradigms": ["oo", "functional"], "exts": [".dart"], "targets": ["flutter", "web", "mobile"]},
    {"id": "ruby", "name": "Ruby", "family": "scripting", "paradigms": ["oo", "dynamic"], "exts": [".rb", ".erb"], "targets": ["web", "scripting"]},
    {"id": "php", "name": "PHP", "family": "web", "paradigms": ["oo", "imperative"], "exts": [".php", ".phtml"], "targets": ["web", "backend"]},
    {"id": "perl", "name": "Perl", "family": "scripting", "paradigms": ["imperative", "dynamic"], "exts": [".pl", ".pm"], "targets": ["scripting", "text"]},
    {"id": "lua", "name": "Lua", "family": "scripting", "paradigms": ["imperative", "embeddable"], "exts": [".lua"], "targets": ["embedded", "games", "config"]},
    {"id": "scala", "name": "Scala", "family": "jvm", "paradigms": ["functional", "oo"], "exts": [".scala", ".sc"], "targets": ["backend", "data", "spark"]},
    {"id": "groovy", "name": "Groovy", "family": "jvm", "paradigms": ["oo", "dynamic"], "exts": [".groovy", ".gradle"], "targets": ["jvm", "build"]},
    {"id": "objectpascal", "name": "Object Pascal / Delphi", "family": "pascal", "paradigms": ["oo", "imperative"], "exts": [".pas", ".pp", ".dpr"], "targets": ["desktop", "windows"]},
    # --- Fonctionnels / académiques ---
    {"id": "haskell", "name": "Haskell", "family": "functional", "paradigms": ["functional", "lazy", "typed"], "exts": [".hs", ".lhs"], "targets": ["research", "backend"]},
    {"id": "ocaml", "name": "OCaml", "family": "functional", "paradigms": ["functional", "oo"], "exts": [".ml", ".mli"], "targets": ["research", "systems"]},
    {"id": "elixir", "name": "Elixir", "family": "beam", "paradigms": ["functional", "concurrent"], "exts": [".ex", ".exs"], "targets": ["backend", "distributed"]},
    {"id": "erlang", "name": "Erlang", "family": "beam", "paradigms": ["functional", "concurrent"], "exts": [".erl", ".hrl"], "targets": ["telecom", "distributed"]},
    {"id": "clojure", "name": "Clojure", "family": "jvm-lisp", "paradigms": ["functional", "lisp"], "exts": [".clj", ".cljs", ".cljc", ".edn"], "targets": ["backend", "web"]},
    {"id": "lisp", "name": "Common Lisp", "family": "lisp", "paradigms": ["functional", "meta"], "exts": [".lisp", ".lsp", ".cl"], "targets": ["research", "ai"]},
    {"id": "scheme", "name": "Scheme", "family": "lisp", "paradigms": ["functional"], "exts": [".scm", ".ss"], "targets": ["research", "teaching"]},
    {"id": "racket", "name": "Racket", "family": "lisp", "paradigms": ["functional", "meta"], "exts": [".rkt"], "targets": ["research", "teaching"]},
    {"id": "fortran", "name": "Fortran", "family": "scientific", "paradigms": ["imperative", "array"], "exts": [".f", ".f90", ".f95", ".for"], "targets": ["hpc", "science"]},
    {"id": "julia", "name": "Julia", "family": "scientific", "paradigms": ["multiple-dispatch", "scientific"], "exts": [".jl"], "targets": ["science", "ml", "hpc"]},
    {"id": "r", "name": "R", "family": "data", "paradigms": ["functional", "array"], "exts": [".r", ".R", ".rmd"], "targets": ["stats", "data"]},
    {"id": "matlab", "name": "MATLAB", "family": "scientific", "paradigms": ["array", "imperative"], "exts": [".m"], "targets": ["science", "engineering"]},
    {"id": "cobol", "name": "COBOL", "family": "legacy", "paradigms": ["imperative"], "exts": [".cob", ".cbl"], "targets": ["mainframe", "finance"]},
    {"id": "ada", "name": "Ada", "family": "systems", "paradigms": ["oo", "concurrent", "safe"], "exts": [".adb", ".ads"], "targets": ["aerospace", "defense", "embedded"]},
    # --- Shells / automatisation ---
    {"id": "bash", "name": "Bash / Shell", "family": "shell", "paradigms": ["imperative"], "exts": [".sh", ".bash"], "targets": ["scripting", "devops"]},
    {"id": "powershell", "name": "PowerShell", "family": "shell", "paradigms": ["oo", "pipeline"], "exts": [".ps1", ".psm1", ".psd1"], "targets": ["windows", "devops", "automation"]},
    {"id": "batch", "name": "Batch (cmd)", "family": "shell", "paradigms": ["imperative"], "exts": [".bat", ".cmd"], "targets": ["windows"]},
    {"id": "zsh", "name": "Zsh", "family": "shell", "paradigms": ["imperative"], "exts": [".zsh"], "targets": ["scripting"]},
    # --- Requêtes / données ---
    {"id": "sql", "name": "SQL", "family": "query", "paradigms": ["declarative"], "exts": [".sql"], "targets": ["mysql", "postgres", "sqlite", "mssql", "oracle"]},
    {"id": "graphql", "name": "GraphQL", "family": "query", "paradigms": ["declarative"], "exts": [".graphql", ".gql"], "targets": ["api"]},
    {"id": "sparql", "name": "SPARQL", "family": "query", "paradigms": ["declarative"], "exts": [".rq"], "targets": ["rdf", "semantic"]},
    # --- Web / balisage / style / config ---
    {"id": "html", "name": "HTML", "family": "markup", "paradigms": ["markup"], "exts": [".html", ".htm"], "targets": ["web"]},
    {"id": "css", "name": "CSS", "family": "style", "paradigms": ["declarative"], "exts": [".css"], "targets": ["web"]},
    {"id": "scss", "name": "Sass/SCSS", "family": "style", "paradigms": ["declarative"], "exts": [".scss", ".sass"], "targets": ["web"]},
    {"id": "vue", "name": "Vue SFC", "family": "web", "paradigms": ["component"], "exts": [".vue"], "targets": ["web"]},
    {"id": "svelte", "name": "Svelte", "family": "web", "paradigms": ["component"], "exts": [".svelte"], "targets": ["web"]},
    {"id": "json", "name": "JSON", "family": "config", "paradigms": ["data"], "exts": [".json", ".jsonc"], "targets": ["config", "data"]},
    {"id": "yaml", "name": "YAML", "family": "config", "paradigms": ["data"], "exts": [".yaml", ".yml"], "targets": ["config", "devops"]},
    {"id": "toml", "name": "TOML", "family": "config", "paradigms": ["data"], "exts": [".toml"], "targets": ["config"]},
    {"id": "xml", "name": "XML", "family": "markup", "paradigms": ["markup"], "exts": [".xml", ".xsd", ".xsl"], "targets": ["config", "data"]},
    {"id": "markdown", "name": "Markdown", "family": "markup", "paradigms": ["markup"], "exts": [".md", ".markdown"], "targets": ["docs"]},
    {"id": "dockerfile", "name": "Dockerfile", "family": "config", "paradigms": ["declarative"], "exts": [".dockerfile"], "targets": ["devops"]},
    {"id": "terraform", "name": "Terraform (HCL)", "family": "config", "paradigms": ["declarative"], "exts": [".tf", ".tfvars"], "targets": ["iac", "cloud"]},
    # --- Systèmes spécialisés / autres ---
    {"id": "assembly", "name": "Assembly", "family": "low-level", "paradigms": ["imperative"], "exts": [".asm", ".s"], "targets": ["systems", "embedded"]},
    {"id": "wasm", "name": "WebAssembly", "family": "low-level", "paradigms": ["stack"], "exts": [".wat", ".wasm"], "targets": ["web", "portable"]},
    {"id": "solidity", "name": "Solidity", "family": "blockchain", "paradigms": ["contract"], "exts": [".sol"], "targets": ["ethereum", "smart-contracts"]},
    {"id": "zig", "name": "Zig", "family": "systems", "paradigms": ["systems", "safe"], "exts": [".zig"], "targets": ["systems", "embedded"]},
    {"id": "nim", "name": "Nim", "family": "systems", "paradigms": ["oo", "systems"], "exts": [".nim"], "targets": ["systems", "scripting"]},
    {"id": "crystal", "name": "Crystal", "family": "general", "paradigms": ["oo", "typed"], "exts": [".cr"], "targets": ["backend"]},
    {"id": "haxe", "name": "Haxe", "family": "general", "paradigms": ["oo", "cross"], "exts": [".hx"], "targets": ["cross-platform", "games"]},
    {"id": "verilog", "name": "Verilog", "family": "hdl", "paradigms": ["hardware"], "exts": [".v", ".sv"], "targets": ["fpga", "asic"]},
    {"id": "vhdl", "name": "VHDL", "family": "hdl", "paradigms": ["hardware"], "exts": [".vhd", ".vhdl"], "targets": ["fpga", "asic"]},
    {"id": "prolog", "name": "Prolog", "family": "logic", "paradigms": ["logic"], "exts": [".pro"], "targets": ["ai", "research"]},
    {"id": "tcl", "name": "Tcl", "family": "scripting", "paradigms": ["imperative"], "exts": [".tcl"], "targets": ["scripting", "eda"]},
    {"id": "groovy_pipeline", "name": "Jenkinsfile", "family": "config", "paradigms": ["declarative"], "exts": [".jenkinsfile"], "targets": ["ci"]},
    {"id": "gdscript", "name": "GDScript", "family": "games", "paradigms": ["oo", "dynamic"], "exts": [".gd"], "targets": ["godot", "games"]},
    {"id": "glsl", "name": "GLSL", "family": "shader", "paradigms": ["shader"], "exts": [".glsl", ".vert", ".frag"], "targets": ["graphics", "gpu"]},
    {"id": "hlsl", "name": "HLSL", "family": "shader", "paradigms": ["shader"], "exts": [".hlsl"], "targets": ["directx", "gpu"]},
    {"id": "wgsl", "name": "WGSL", "family": "shader", "paradigms": ["shader"], "exts": [".wgsl"], "targets": ["webgpu", "gpu"]},
    {"id": "metal", "name": "Metal Shading Language", "family": "shader", "paradigms": ["shader"], "exts": [".metal"], "targets": ["apple", "gpu"]},
]

# Index extension -> langage (construit une fois).
_EXT_INDEX: dict[str, dict] = {}
for _lang in LANGUAGES:
    for _e in _lang["exts"]:
        _EXT_INDEX[_e.lower()] = _lang


def all_languages() -> list[dict]:
    return LANGUAGES


def language_count() -> int:
    return len(LANGUAGES)


def detect_by_extension(path: str) -> dict | None:
    """Détecte le langage d'un fichier par son extension (ou nom spécial)."""
    low = path.lower().replace("\\", "/")
    name = low.rsplit("/", 1)[-1]
    # Noms de fichiers spéciaux sans extension classique.
    specials = {
        "dockerfile": "dockerfile", "makefile": "makefile", "jenkinsfile": "groovy_pipeline",
        "cmakelists.txt": "cmake", "gemfile": "ruby", "rakefile": "ruby",
    }
    if name in specials:
        lid = specials[name]
        for lang in LANGUAGES:
            if lang["id"] == lid:
                return lang
        return {"id": lid, "name": lid, "family": "config", "paradigms": [], "exts": [], "targets": []}
    for ext, lang in _EXT_INDEX.items():
        if name.endswith(ext):
            return lang
    return None


def by_id(lang_id: str) -> dict | None:
    for lang in LANGUAGES:
        if lang["id"] == lang_id:
            return lang
    return None


def families() -> dict[str, int]:
    out: dict[str, int] = {}
    for lang in LANGUAGES:
        out[lang["family"]] = out.get(lang["family"], 0) + 1
    return out
