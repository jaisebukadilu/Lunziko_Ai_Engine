# Lunziko Code Intelligence — Intégrations (tous les outils de code)

> Objectif : utiliser **Lunziko Code Intelligence** depuis n'importe quel environnement où l'on écrit
> ou exécute du code. Trois surfaces standard le rendent universel :
>
> | Surface | Endpoint | Consommé par |
> |---------|----------|--------------|
> | **OpenAI-compatible** | `POST /v1/chat/completions`, `/v1/embeddings`, `/v1/models` | VS Code, JetBrains, Android Studio, Visual Studio, Sublime, Cursor, Windsurf, Open WebUI |
> | **MCP (Model Context Protocol)** | `POST /mcp` (outils `code_*`) | Cursor, Claude Desktop, Cline, Continue, **Antigravity**, VS Code MCP |
> | **REST + CLI** | `/v1/code-intelligence/*` + `scripts/lzcode.py` | PowerShell, Xcode, terminal, GitHub Actions, Docker |
>
> Gateway par défaut : `http://127.0.0.1:8770`. Auth optionnelle : en-tête `X-API-Key`.
> Lancer : `uvicorn ai_engine.gateway.main:app --port 8770`.

---

## 1. PowerShell / terminal

```powershell
$env:AE_URL = "http://127.0.0.1:8770"
python scripts/lzcode.py understand .
python scripts/lzcode.py index . --project mon-app
python scripts/lzcode.py search mon-app "où est la facturation ?"
python scripts/lzcode.py detect .\scripts\deploy.ps1
```

Fonction PowerShell pratique (à mettre dans `$PROFILE`) :

```powershell
function lzcode { python "C:\Users\Joe\Desktop\Lunziko\Lunziko AI Engine\lunziko-ai-engine\scripts\lzcode.py" @args }
```

## 2. VS Code

- **Continue** (open source) ou **Cline** : ajouter un modèle « OpenAI-compatible »
  base URL `http://127.0.0.1:8770/v1`, apiKey = votre `X-API-Key`, model `lunziko-auto`.
- **MCP** : VS Code (Agent/Copilot MCP) → serveur `http://127.0.0.1:8770/mcp` : les outils
  `code_understand`, `code_search`, `code_dependencies`, `code_detect_language`,
  `code_project_context` deviennent disponibles à l'agent.

## 3. Xcode

Xcode n'a pas d'API d'extension IA officielle → deux voies :
- **Behavior / Build Phase** : un *Run Script* appelle `lzcode.py` (ex. `understand`, `search`)
  et affiche le résultat dans les logs de build.
- **Terminal intégré** : `lzcode` directement (voir §1) sur le dossier du projet Swift/Obj-C.
  Détection native `.swift/.m/.mm/.metal` + symboles `func/class/struct`.

## 4. Visual Studio (Windows)

- Extensions supportant un endpoint OpenAI custom (Continue for VS, CodeGPT) → base URL
  `http://127.0.0.1:8770/v1`.
- **External Tools** (Menu *Tools → External Tools*) : commande `python`, args
  `scripts\lzcode.py understand $(SolutionDir)`.

## 5. Sublime Text

- Package **LSP-AI** ou **CodeGPT/OpenAI** : configurer l'URL OpenAI custom `…/v1`.
- Ou *Build System* custom exécutant `lzcode.py` sur le fichier/projet courant.

## 6. JetBrains (IntelliJ, PyCharm, WebStorm, Rider, CLion…)

- Plugin **Continue** ou **CodeGPT** → provider OpenAI custom, base URL `…/v1`, `lunziko-auto`.
- **MCP** : plugins JetBrains MCP → `http://127.0.0.1:8770/mcp`.
- **External Tools** : `lzcode.py` avec `$ProjectFileDir$`.

## 7. Android Studio

Basé sur IntelliJ → identique à §6 (Continue/CodeGPT OpenAI-compatible + External Tools).
Détection native `.kt/.kts/.java/.gradle`.

## 8. Docker

- Lancer l'AI Engine : `docker run -p 8770:8770 jaisebukadilu/lunziko-ai-engine`.
- Analyser un projet conteneurisé : monter le code puis `lzcode understand /workspace`.
- Code Intelligence détecte `Dockerfile` et extrait les dépendances multi-écosystèmes.

## 9. Microsoft SQL Server / PostgreSQL

- Langage `sql` reconnu (`.sql`), indexation + recherche sémantique des scripts/migrations,
  extraction de symboles (procédures, vues via patterns).
- **Data Brain** + `/v1/data/*` pour comprendre schémas et générer des requêtes.
- Persistance : l'AI Engine peut lui-même tourner sur **PostgreSQL/pgvector**
  (`AE_STORAGE_BACKEND=postgres`, `AE_VECTOR_BACKEND=pgvector`) — voir `DATABASE`/config.

## 10. GitHub

- **GitHub Actions** : étape qui interroge Code Intelligence (l'engine tourne en service) :

```yaml
- name: Lunziko Code Intelligence
  run: |
    python scripts/lzcode.py understand .
    python scripts/lzcode.py deps .
  env:
    AE_URL: http://127.0.0.1:8770
    AE_API_KEY: ${{ secrets.AE_API_KEY }}
```

- Outils Git/GitHub via le Code Brain (garde-fous avant toute modification destructive).

## 11. Antigravity (IDE agentique)

- **MCP** : ajouter le serveur `http://127.0.0.1:8770/mcp` → les outils `code_*` et tous les
  outils du ToolRegistry (ecosystem_search, web_search…) deviennent utilisables par l'agent.
- **OpenAI-compatible** : configurer `…/v1` + `lunziko-auto` comme modèle si un provider custom
  est accepté.

---

## Résumé des endpoints Code Intelligence

| Méthode | Route | Rôle |
|---------|-------|------|
| GET  | `/v1/code-intelligence/languages` | Catalogue des langages (60+) + familles |
| GET  | `/v1/code-intelligence/detect?path=` | Détection du langage d'un fichier |
| POST | `/v1/code-intelligence/index` | Indexe un dépôt (recherche sémantique) |
| POST | `/v1/code-intelligence/search` | Recherche sémantique dans le code indexé |
| GET  | `/v1/code-intelligence/understand?root=` | Architecture (langages, entrées, manifestes) |
| GET  | `/v1/code-intelligence/dependencies?root=` | Dépendances déclarées (npm/pip/cargo/go/…) |
| POST | `/v1/code-intelligence/symbols` | Extraction de symboles (fonctions/classes/…) |
| GET  | `/v1/code-intelligence/projects` | Projets indexés |
| GET  | `/v1/code-intelligence/project/{p}` | Contexte écosystème d'un projet Lunziko |

Les mêmes capacités sont exposées comme **outils MCP** (`code_detect_language`, `code_understand`,
`code_search`, `code_dependencies`, `code_project_context`, `code_write`, `code_edit`) et donc
pilotables par n'importe quel agent/éditeur compatible MCP ou OpenAI tool-calling.

## Écriture contrôlée de fichiers (avec garde-fous)

| Méthode | Route | Rôle |
|---------|-------|------|
| POST | `/v1/code-intelligence/write` | Crée/écrase un fichier (dry-run par défaut) |
| POST | `/v1/code-intelligence/edit` | Remplace un `old_string` **unique** (str-replace sûr) |
| POST | `/v1/code-intelligence/delete` | Suppression **soft** (sauvegardée, réversible) |
| POST | `/v1/code-intelligence/restore/{backup_id}` | Restaure une sauvegarde |
| GET  | `/v1/code-intelligence/backups` | Liste des sauvegardes |
| GET  | `/v1/code-intelligence/git/{status,diff,log}` | Lecture Git |
| POST | `/v1/code-intelligence/git/checkpoint` | Branche de sécurité + commit **avant** édition |
| POST | `/v1/code-intelligence/git/commit` | Commit local (jamais de push auto) |

**Garde-fous (garantie « aucune action destructive sans filet ») :**
- **dry-run par défaut** : sans `confirm=true`, on renvoie un **diff** sans rien écrire ;
- **sandbox de chemin** : refus du `..` et de tout chemin hors `root` (option `AE_CODEINTEL_WORKSPACE`) ;
- **zones protégées** : `.git/`, `node_modules/`, `.venv/`, `.env`, clés SSH… ;
- **sauvegarde réversible** avant tout écrasement/suppression → `restore` ;
- **Git** : jamais de `push`/`reset --hard`/`clean`/`rebase` ; `checkpoint` crée un filet avant édition.
