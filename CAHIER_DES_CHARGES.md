# Cahier des charges — Lunziko AI Engine

> **Version du document :** 1.0 — 16 août 2026 (état *as-built*, reflète le code livré)
> **Dépôt :** `github.com/jaisebukadilu/Lunziko_Ai_Engine` (branche `main`)
> **Image Docker :** `jaisebukadilu/lunziko-ai-engine:latest` · `:0.1.0`

---

## 1. Contexte & positionnement

**Lunziko AI Engine** est le **système d'intelligence orchestrée** de l'écosystème Lunziko.
Il combine plusieurs cerveaux spécialisés (**AI Brains**), plusieurs moteurs d'exécution et de
connaissance (**AI Engines**), des agents et des outils afin de **comprendre une tâche,
sélectionner les capacités appropriées, collaborer entre applications Lunziko, exécuter les
opérations, vérifier les résultats et accompagner l'utilisateur** jusqu'à la finalisation.

Architecture globale : **LAIA — Lunziko AI Intelligence Architecture** (Multi-Brain / Multi-Engine).
Principe directeur :
> **One AI Engine → Multiple Brains → Multiple Engines → Multiple Agents → Multiple Tools → One Unified Intelligence.**

### Principes fondateurs (non négociables)
- **Indépendance de Platform** : fonctionne 100 % en local par défaut (persistance enfichable,
  providers propres). Platform et les applications sont des **clients optionnels** ; l'AI Engine
  ne modifie jamais Platform.
- **Construit au-dessus de l'existant** : LAIA ajoute une couche méta ; les 28 modules ne sont
  jamais remplacés, ils deviennent des « Engines ».
- **Clean-room** : aucun code tiers copié ; inspiration conceptuelle uniquement (licences respectées).
- **Sûr par défaut** : exécution de code désactivée par défaut ; garde-fous (Safety Engine).
- **Frontière écosystème** : identité / RBAC / licences = **Lunziko Platform** (consommées, jamais recodées).

---

## 2. Périmètre fonctionnel

L'AI Engine expose un **gateway REST FastAPI** (port `8770`) regroupant **28 modules**.

### 2.1 Intelligence & génération
| Capacité | Endpoints | État |
|---|---|---|
| Provider Manager (cloud + local + natif) | `POST /v1/chat`, `GET /v1/providers` | ✅ |
| Endpoints compatibles OpenAI (drop-in) | `POST /v1/chat/completions`, `/embeddings`, `GET /v1/models` | ✅ |
| Embeddings & RAG | `POST /v1/embed`, `/v1/rag/{index,search,query}` | ✅ |
| LLM natif `lunziko` (paquet `lunziko-llm`, from scratch) | provider `lunziko` | ✅ (jouet, scalable) |

### 2.2 Mémoire, connaissance & contexte
| Capacité | Endpoints | État |
|---|---|---|
| Mémoire chiffrée AES-256-GCM | `/v1/memory/{save,list,recall}` | ✅ |
| Knowledge graph (auto-linking) | `/v1/knowledge/{add,search,relations}` | ✅ |
| Écosystème (ingestion du registre maître) | `/v1/ecosystem/{status,sync,apps,search}` | ✅ |
| Activité (journal d'actions, contexte comportemental) | `/v1/activity/{log,timeline,search,summary}` | ✅ |
| Couche de Contexte Unifié (A-14→A-18) | `/v1/context/assemble`, `/v1/appstate`, `/v1/profile/*` | ✅ |
| Feedback (retours → few-shot) | `/v1/feedback/{,stats,corrections}` | ✅ |
| Catalogue de schémas de données | `/v1/catalog/{register,schemas,resolve}` | ✅ |
| Connecteurs RAG (docs/chat/mail/fichiers, recherche unifiée) | `/v1/connectors/{types,ingest,search}` | ✅ |

### 2.3 Raisonnement, agents & action
| Capacité | Endpoints | État |
|---|---|---|
| Agents contextuels + routeur d'intention neuronal hybride | `/v1/agent/{run,capabilities}` | ✅ |
| Système neuronal (backends + ML + inférence) | `/v1/neural/{status,backends,route,train,ml/*,inference}` | ✅ |
| Données (profilage/nettoyage/préparation) | `/v1/data/{profile,clean,prepare-*}` | ✅ |
| Tool-calling natif (A-4b) | `/v1/tools`, `/v1/tools/run`, `/v1/agent/act` | ✅ |
| MCP (Model Context Protocol, serveur + client) | `POST /mcp`, `/v1/mcp/import` | ✅ |
| Workflows & Automatisation (nœuds, clean-room n8n) | `/v1/workflow/*`, `/v1/automation/*` | ✅ |
| Action Registry (actions d'app exécutables) | `/v1/actions/{register,invoke}` | ✅ |
| Assistant scopé par application (≤ 5 agents) + WebSocket | `/v1/assistant/{app}/*`, `WS .../ws` | ✅ |
| Handoff inter-apps (redirection/transfert/ouverture) | `/v1/handoff/{redirect,open-with,transfer}` | ✅ |

### 2.4 LAIA (couche d'orchestration) & moteurs transverses
| Capacité | Endpoints | État |
|---|---|---|
| Brain Registry (16 cerveaux) | `/v1/brains/*` | ✅ |
| Engine Registry (mappe les modules) | `/v1/engines/*` | ✅ |
| AI Orchestrator (plan/run, décomposition, collaboration) | `/v1/orchestrator/{plan,run}` | ✅ |
| AI Blackboard (état de tâche partagé) | `/v1/blackboard/tasks/*` | ✅ |
| App Requirements (besoins Brains/Engines par app) | `/v1/apps/{app}/requirements` | ✅ |
| Validation Engine | `/v1/validate` | ✅ |
| Evaluation Engine (score/qualité) | `/v1/evaluate` | ✅ |
| Safety Engine (PII / injection / modération) | `/v1/safety/{check,redact}` | ✅ |
| Code Execution Engine (A-11, sûr par défaut) | `/v1/code-exec/{status,eval,run}` | ✅ |
| Pont Graphics Engine (client REST) | `/v1/graphics/{status,ping,brains,call}` | ✅ connecté |
| Voix (STT/MT/TTS, 18 packs) | `/v1/voice/*` | ⏳ 501 (V-1→V-3) |

### 2.5 Catalogue des Brains
- **Actifs** (servis par providers/engines) : `text`, `reasoning`, `code`, `data`, `research`,
  `document`, `ui_ux`, `language`.
- **Multimédias** (déclarés → **actifs quand le Graphics Engine est branché**) : `vision`,
  `image`, `video`, `3d`, `cad` ; + `audio`, `music`, `voice` (nécessitent des modèles dédiés).

---

## 3. Exigences techniques

### 3.1 Architecture logicielle
- **Cœur Python / FastAPI** (gateway `ai_engine.gateway.main:app`).
- **Architecture hexagonale** : le cœur ne connaît que des **ports** (`StoragePort`, `VectorPort`,
  `BlobPort`) ; adaptateurs locaux par défaut (SQLite / vecteur local / FS), Postgres/pgvector optionnels.
- **Modularité** : chaque module = `engine.py` (logique) + `router.py` (endpoints), monté sur le gateway.
- **LAIA** superpose Orchestrator + Registries + Blackboard + Validation/Evaluation/Safety **sans
  modifier** les modules sous-jacents.

### 3.2 Persistance & indépendance
- Magasin local par défaut : `~/.lunziko/ai-engine/` (`store.db`, `vectors/`, `blobs/`) ou `/data`
  en conteneur (`AI_ENGINE_HOME`).
- Fonctionnement **hors-ligne garanti** : repli embeddings **hash**, cipher dev, providers absents
  tolérés (dégradation propre).

### 3.3 Sécurité
- **Mémoire chiffrée** AES-256-GCM (`AE_MEMORY_KEY`).
- **Safety Engine** : redaction PII (e-mails/téléphones/IBAN/cartes avec Luhn), détection
  d'injection de prompt (FR+EN), modération heuristique.
- **Code Execution** : Niveau 0 safe-eval (AST restreint, réellement sûr) toujours actif ;
  Niveau 1 sandbox subprocess **désactivé par défaut** (`AE_CODE_EXEC_ENABLED`), isolation OS
  requise pour du code non fiable (cf. `CODE_EXECUTION_SANDBOX.md`).
- Auth gateway par clé (`X-API-Key` / `Authorization: Bearer` ; libre en dev).

### 3.4 Performance & robustesse
- Provider Manager avec **fallback en cascade** (claude→chatgpt→gemini→mistral→deepseek→local).
- Routeur d'intention **hybride** (neuronal + lexical) : 12/12 sur jeu difficile.
- Non-régression : **87 tests pytest offline** + **CI GitHub Actions** (Python 3.11/3.12).

### 3.5 Intégration écosystème
- **Registre maître** `REGISTRE_ECOSYSTEME_LUNZIKO.md` ingéré au démarrage (règle « analyse au lancement »).
- **Graphics Engine** (dépôt séparé, REST 93 endpoints / 22 agents) : connecté en client, **non
  modifié** ; les Brains multimédias lui sont **délégués** par l'orchestrateur (`AE_GRAPHICS_ENGINE_URL`).
- **Platform** : consommée (identité/licences) si présente, jamais requise.
- **SDKs clients** : TypeScript, Swift, Kotlin, Dart (`sdk/`).

### 3.6 Déploiement
- **Docker** : `Dockerfile` (python:3.12-slim, `.[secure,neural]`, HEALTHCHECK `/health`),
  `docker-compose.yml`, image publiée sur **Docker Hub** (`jaisebukadilu/lunziko-ai-engine`).
- Guide : `DEPLOY.md`. Volume de persistance `/data`.

---

## 4. Contraintes & règles

- **Clean-room** : aucun code tiers copié (n8n fair-code, Open Interpreter AGPL, OpenNN LGPL exclus ;
  frameworks neuronaux importés en **dépendances optionnelles** BSD/Apache).
- **Ne jamais modifier** : Lunziko Platform, Lunziko Graphics Engine (consommés via API versionnées).
- **Versionnage** : SemVer sur API & schémas ; compatibilité ascendante.
- **Types neutres** : dates ISO 8601, UUID, devises ISO 4217, langues BCP 47.

---

## 5. Livrables (état actuel)

| Livrable | État |
|---|---|
| Code `lunziko-ai-engine/` (28 modules) | ✅ livré, poussé GitHub |
| Paquet `lunziko-llm/` (LLM natif from scratch) | ✅ dépôt dédié |
| Suite de tests (87) + CI | ✅ |
| SDKs TS/Swift/Kotlin/Dart | ✅ |
| Documents : `LAIA_ARCHITECTURE`, `CONTEXT_LAYER_ARCHITECTURE`, `CODE_EXECUTION_SANDBOX`, `DEPLOY`, README | ✅ |
| Image Docker publiée (Docker Hub) | ✅ |
| Connexion Graphics Engine (validée en réel) | ✅ |

---

## 6. Reste à faire (roadmap)

| Item | Bloqueur / nature |
|---|---|
| **V-1→V-3 Voix** (TTS Kokoro / STT Whisper / MT) | téléchargement des modèles |
| **Montée en charge `lunziko-llm`** (PyTorch/GPU, MoE, distribué, SFT/DPO) | matériel (GPU) |
| **Search Engine web** (Research Brain) | accès réseau côté moteur |
| **Modèles génératifs image/3d** (activer pleinement les Brains multimédias) | modèles de génération dédiés |
| **A-9 SDKs Swift/Kotlin** compilés/publiés | toolchains + registres de paquets |

---

## 7. Critères d'acceptation

- [x] Le gateway démarre et `GET /health` liste 28 modules actifs.
- [x] Fonctionnement hors-ligne (embedder hash) sans clé provider.
- [x] 87 tests pytest passent ; CI verte.
- [x] Image Docker build + `docker run` → `/health` OK (28 modules).
- [x] Connexion réelle au Graphics Engine (22 agents) + délégation des Brains multimédias.
- [x] Aucune modification de Platform ni du Graphics Engine (consommés via API).
- [x] Sûr par défaut (sandbox code désactivé ; garde-fous Safety actifs).

---

*Document généré à partir de l'état réel du code (branche `main`). Sources de vérité :
`README.md`, `LAIA_ARCHITECTURE.md`, `REGISTRE_ECOSYSTEME_LUNZIKO.md`.*
