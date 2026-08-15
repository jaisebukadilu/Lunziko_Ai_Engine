# Lunziko AI Engine

IA **autonome et complète** de l'écosystème Lunziko : gateway + provider manager (cloud + local),
mémoire, RAG, agents, workflows, et le module **Voix & Traduction**.

> **Indépendant de Lunziko Platform.** L'AI Engine fonctionne seul (persistance locale, providers
> propres) ; Platform et les applications le **consomment** via son gateway/SDK, sans que Platform
> soit modifié. Voir `../AI_ENGINE_ARCHITECTURE.md` et `../VOICE_ARCHITECTURE.md`.

## Architecture (résumé)

```
ai_engine/
├── gateway/        FastAPI : /health, auth par clé, montage des modules
├── core/
│   ├── ports.py    StoragePort / VectorPort / BlobPort (interfaces)
│   ├── backends/   SQLite (storage) · vecteur local (numpy/pur-py) · FS (blob)
│   └── registry.py câblage des ports selon la config (local par défaut)
└── modules/
    ├── provider/   Provider Manager autonome (claude/chatgpt/gemini/mistral/deepseek/local) + fallback
    ├── embeddings/ Génération de vecteurs (openai/mistral/gemini/local + repli hash hors-ligne)
    ├── rag/        Chunking + indexation VectorPort + recherche + réponse augmentée
    ├── memory/     Mémoire utilisateur chiffrée AES-256-GCM + rappel sémantique
    ├── knowledge/  Graphe de connaissances (items typés + relations auto-liées)
    ├── agents/     Assistant contextuel (capacité + mémoire + knowledge + provider)
    ├── workflows/  Pipelines multi-étapes composant les modules (runs persistés)
    ├── code/       Analyse/débogage/explication de code (modèles locaux Ollama en priorité)
    ├── openai_api/ Endpoints compatibles OpenAI (drop-in Open WebUI/LocalAI/Continue)
    ├── ecosystem/  Ingestion du registre maître Lunziko (apps + fonctions) au démarrage
    ├── activity/   Journal d'actions utilisateur (contexte comportemental, detail chiffré)
    ├── neural/     Système neuronal : backends + routeur d'intention + entraîneur ML + moteurs d'inférence
    ├── data/       Pilier données : profilage, nettoyage, préparation (RAG/corpus/entraînement)
    ├── assistant/  Assistant scopé par app (zone de compétence) + agents (≤5) + WebSocket/UI + sessions
    ├── handoff/    Redirection inter-apps + transfert/ouverture de fichiers vers l'app adaptée
    ├── tools/      Tool-calling : registre d'outils + boucle d'exécution (agents qui agissent)
    ├── mcp/        Model Context Protocol : serveur (expose les outils) + client (importe des serveurs externes)
    ├── context/    Couche de Contexte : profil & habitudes + état applicatif live + assembleur unifié
    ├── feedback/   Retours utilisateur (up/down + corrections) → stats + few-shot
    ├── catalog/    Schémas de données publiés par les apps + résolution sémantique
    ├── automation/ Moteur de flux par nœuds (chaîne des outils ; clean-room n8n)
    └── voice/      STT · MT · TTS · 10 voix · packs de langues (18)

sdk/typescript/     Client @lunziko/ai-engine (fetch) pour Platform / web / apps
sdk/swift/          Client Swift (async/await) — macOS/iOS
sdk/kotlin/         Client Kotlin (java.net.http) — JVM/Android
sdk/dart/           Client Dart (package:http) — Flutter
core/backends/      + postgres_storage · pg_vector (couplage optionnel Platform)
```

## État

- **A-0 ✅** socle réorganisé : gateway + ports de persistance (local par défaut) + module voix migré.
- **A-1 ✅** Provider Manager autonome + `POST /v1/chat` (REST direct via httpx, pile permissive).
- **A-2 ✅** Embeddings (`/v1/embed`) + RAG (`/v1/rag/{index,search,query}`) sur le VectorPort ;
  repli embedding **hash hors-ligne** garanti (RAG fonctionne sans réseau ni modèle). Récupération
  sémantique validée en test.
- **A-3 ✅** Mémoire chiffrée **AES-256-GCM** (`/v1/memory/{save,list,recall}`, rappel sémantique) +
  **Knowledge graph** (`/v1/knowledge/{add,search,relations}`, auto-linking cosinus ≥ 0.30) sur les
  ports. Chiffrement + rappel + auto-linking validés en test offline. AES-GCM réel : extra `secure`.
- **A-4 ✅** **Agents** (`/v1/agent/run`, sélection de capacité + contexte mémoire/knowledge + provider) +
  **Workflows** (`/v1/workflow/{types,run,runs}`, pipelines composables, runs persistés). Exécuteur +
  routage validés en test offline. Tool-calling natif = amélioration ultérieure (A-4b).
- **A-5 (partiel) ✅** Adaptateurs **Postgres/pgvector** (couplage optionnel Platform : `AE_STORAGE_BACKEND=postgres`
  / `AE_VECTOR_BACKEND=pgvector` + DSN ; import paresseux, extra `postgres`) + **SDK TypeScript**
  `@lunziko/ai-engine` (`sdk/typescript/`). SDKs Swift/Kotlin/Dart : à venir.
- **A-6 ✅** **Code & Logique** (`/v1/code/{analyze,debug,explain}`) — priorité aux **modèles locaux Ollama**
  (Qwen-Coder / DeepSeek-Coder / CodeLlama via `AE_LOCAL_BASE_URL` + `AE_CODE_MODEL`, privé/hors-ligne),
  repli DeepSeek puis cascade. Cf. `../CODE_LOGIC_MODELS.md`.
- **A-8 ✅** **Endpoints compatibles OpenAI** (`/v1/chat/completions` avec pseudo-streaming SSE, `/v1/embeddings`,
  `/v1/models`), auth `Authorization: Bearer` ou `X-API-Key` → **drop-in Open WebUI / LocalAI / Continue / Cline**,
  réutilise le ProviderManager (routage+fallback). Vrai streaming token-par-token = suivi. Cf. `../INTEROP_AND_PLATFORMS.md`.
- **Couche de Contexte Unifié ✅ (A-14→A-16)** (`/v1/context/assemble`, `/v1/appstate`, `/v1/profile/*`) — l'IA
  d'application dispose d'un **contexte temps réel** : **profil & habitudes** (A-14, habitudes dérivées de
  l'activité ; identité/RBAC = Platform consommée, jamais recodée), **état applicatif live éphémère** (A-16,
  écran/brouillon/erreur, TTL, purge à la lecture), et un **assembleur** (A-15) qui unifie profil + habitudes +
  activité + état live + connaissance + app écosystème sous budget, avec contexte **temporel/spatial**, et
  produit un bloc `system` prêt à injecter. Cf. `CONTEXT_LAYER_ARCHITECTURE.md`.
- **Feedback ✅ (A-18)** (`/v1/feedback`, `/v1/feedback/{stats,corrections}`) — corrections/validations (up/down +
  correction) persistées → **statistiques de satisfaction** + **few-shot** réutilisable (`as_fewshot`) pour
  affiner les réponses futures.
- **Catalogue de schémas ✅ (A-17)** (`/v1/catalog/{register,schemas,resolve}`) — les apps publient leurs
  **schémas de données** (champs/types/description) ; **résolution sémantique** pour retrouver le schéma
  pertinent à partir d'une question. L'IA comprend les données manipulées.
- **SDKs multiplateformes ✅ (A-9)** — clients pour le gateway en **TypeScript** (`sdk/typescript/`), **Swift**
  (`sdk/swift/`, async/await macOS/iOS), **Kotlin** (`sdk/kotlin/`, JVM/Android) et **Dart** (`sdk/dart/`, Flutter).
  Surface commune : chat/embed/RAG/mémoire/agent/**act (outils)**/écosystème/activité/contexte/assistant/handoff/
  neural/data/automation + `get`/`post` génériques. SDK Dart validé (`dart analyze` OK) ; Swift/Kotlin écrits en
  miroir (non compilés ici, toolchains absentes).
- **Automatisation ✅ (A-10)** (`/v1/automation/flows`, `.../run`, `.../runs`) — **moteur de flux par nœuds**
  (clean-room, inspiré n8n) : un flux enchaîne des nœuds, chaque nœud appelle un **outil** du registre (A-4b)
  avec des arguments référençant l'entrée (`$input.x`) ou la sortie d'un nœud précédent (`$node.champ`). Flux et
  exécutions persistés. Réimplémenté from scratch (aucun code copié).
- **MCP ✅ (A-7)** (`POST /mcp` JSON-RPC 2.0, `GET /mcp`, `POST /v1/mcp/import`) — **serveur MCP** exposant les
  outils de l'AI Engine (`initialize`/`tools/list`/`tools/call`) → consommable par Claude Desktop / Cline /
  Continue ; **client MCP** qui consomme un serveur MCP externe et **importe ses outils** dans le registre local
  (les agents `/v1/agent/act` peuvent alors les appeler). Standard ouvert (MIT), testé en process.
- **Tool-calling natif ✅ (A-4b)** (`/v1/tools`, `/v1/tools/run`, `/v1/agent/act`) — les agents **agissent** :
  registre d'outils (nom + description + schéma JSON + handler) avec **outils intégrés** branchés sur les
  capacités existantes (`ecosystem_search`, `handoff_open_with`, `data_clean_text`, `ml_predict`,
  `activity_timeline`), **boucle d'exécution** provider-agnostique (le modèle demande un outil → exécution →
  re-boucle → réponse) et **tool-calling** implémenté pour Claude et les providers OpenAI-compatibles
  (ChatGPT/Mistral/DeepSeek/local). Testé offline (boucle avec provider factice + parseurs).
- **Handoff inter-applications ✅** (`/v1/handoff/{redirect,open-with,transfer,file-types}`) — depuis une app,
  selon la situation : **rediriger** l'utilisateur vers l'app Lunziko compétente pour poursuivre sa tâche,
  **transférer** un fichier/dossier vers une autre app, ou **l'ouvrir dans l'app la plus adaptée** (résolution
  par **type de fichier** — table `.xlsx→MySheet`, `.dwg→CAD`, `.png→Photo`, `.ifc→BIM`… — sinon recherche
  sémantique dans le registre). Produit des **actions structurées** (deep-link, executor host/HUB/Platform)
  que l'app hôte exécute. Intégré à l'assistant : hors périmètre → action de redirection attachée à la réponse.
- **Assistant d'application ✅** (`/v1/assistant/{app}/...` + WebSocket) — **intégrable à toutes les apps Lunziko**,
  chaque assistant **limité à la zone de compétence** de son app (fonctions issues du registre écosystème) :
  assiste, corrige, agit dans ce périmètre et **redirige hors périmètre** (garde de scope via recherche
  écosystème). **Jusqu'à 5 agents par application** (rôles spécialisés, plafond appliqué) pour fluidifier les
  tâches (`/agents`, `/team`). **Connexion prête pour une interface visuelle future** : **WebSocket**
  `/v1/assistant/{app}/ws` (événements `ready`/`answer`/`error`), **contrat UI** (`/ui-contract` : actions
  rapides, agents, points de connexion) et **sessions** persistées (`/sessions`).
- **Données ✅** (`/v1/data/{profile,clean,clean-text,prepare-rag,prepare-corpus,prepare-training}`) — pilier
  « matière première » : **profilage** (types, nuls, distincts), **nettoyage** tabulaire (trim, normalisation,
  coercition de types, valeurs manquantes, **déduplication**, lignes vides) et **nettoyage de corpus texte**
  (normalisation, dédup, filtre de longueur), puis **préparation** vers RAG / corpus du LLM natif / table
  d'entraînement ML. Pur Python, offline. Inspiration clean-room OpenRefine/KNIME (aucun code copié).
- **Apprentissage ML ✅** (`/v1/neural/ml/{train,predict,models}`) — pilier « apprendre à partir d'exemples » :
  entraîne un classifieur supervisé (embeddings → softmax NumPy, ou scikit-learn si présent) à partir de paires
  (texte, label), **persisté** et rechargeable. Se combine au module `data` (prépare → entraîne → prédit).
- **Moteurs d'inférence ✅** (`/v1/neural/inference`) — catalogue des serveurs locaux consommables
  (Ollama, llama.cpp, vLLM, LM Studio, Triton + LLM natif `lunziko`) via le Provider Manager (OpenAI-compat).
- **Système neuronal ✅** (`/v1/neural/{status,backends,route,train}`) — couche d'abstraction au-dessus des
  **bibliothèques neuronales** : backend **NumPy natif** (offline) + adaptateurs **optionnels** PyTorch /
  TensorFlow / Keras / JAX / **scikit-learn** / **Transformers** (import paresseux, jamais requis pour démarrer ;
  installer via extras `neural` / `neural-deep` / `neural-hf`). Capacité concrète : **routeur d'intention
  HYBRIDE** — classifieur neuronal (embeddings L2 → softmax) **fusionné** au signal lexical (taxonomie
  partagée : racines normalisées sans accent, tolérant conjugaisons). Remplace le routage par mots-clés de
  l'AgentEngine, **généralise aux formulations sans mot-clé** (`use_neural_router`, défaut true ; repli
  garanti). Mesuré : **12/12** vs 1/12 pour l'ancien routage mots-clés sur un jeu difficile.
  Licences permissives (BSD/Apache) — **aucun code tiers copié** (⚠️ OpenNN LGPL non embarqué).
- **LLM natif Lunziko ✅** — paquet **`../lunziko-llm/`** (architecture Transformer moderne **from scratch**,
  NumPy clean-room : RoPE/RMSNorm/**GQA**/SwiGLU + micro-autograd + BPE + entraînement, gradient-checké,
  entraîné offline). Branché comme **provider `lunziko`** (100 % local, sans clé) via `AE_LUNZIKO_LLM_CKPT`
  + `AE_LUNZIKO_LLM_TOKENIZER` → utilisable par `/v1/chat` et les endpoints OpenAI-compatibles.
- **A-13 ✅** **Activity & Events** (`/v1/activity/{log,log-batch,timeline,search,summary}` + `DELETE`) — première
  brique de la **Couche de Contexte Unifié** (cf. `../CONTEXT_LAYER_ARCHITECTURE.md`) : les apps publient
  *ce que fait l'utilisateur* → journal append-only + timeline + **recherche sémantique** + résumé LLM ; champ
  libre **chiffré** (cipher mémoire AES-256-GCM), recherche offline (repli hash). **Injecté automatiquement dans
  le contexte des agents** (`use_activity`, défaut true). Prochaines briques : appstate, profile, assembler,
  connecteurs RAG, catalog schémas, feedback (A-14→A-18).
- **A-12 ✅** **Écosystème** (`/v1/ecosystem/{sync,apps,search,status}`) — l'AI Engine **ingère le registre
  maître** `REGISTRE_ECOSYSTEME_LUNZIKO.md` (racine Lunziko) au **démarrage** (règle de gouvernance « analyse
  au lancement ») dans un index local (StoragePort + VectorPort), pour **connaître toutes les applications
  Lunziko et leurs fonctions** et **accompagner l'utilisateur**. Sync idempotente, recherche sémantique
  (repli hash hors-ligne), et **injection automatique dans le contexte des agents** (`/v1/agent/run`). Découverte
  auto du fichier ou override `AE_REGISTRY_PATH` ; désactivable via `AE_REGISTRY_AUTOSYNC=false`.
- **Voix V-0 ✅** health/voices/packs réels ; TTS/STT/MT = `501` jusqu'aux phases V-1→V-3.

## Démarrage (dev)

```bash
cd "Lunziko AI Engine/lunziko-ai-engine"
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env        # y mettre au moins une clé provider (ANTHROPIC_API_KEY, …)
uvicorn ai_engine.gateway.main:app --reload --port 8770
```

Puis : http://localhost:8770/docs · http://localhost:8770/health

## Endpoints

| Route | État |
|-------|------|
| `GET /health` · `GET /` | ✅ |
| `GET /v1/providers` | ✅ providers disponibles (selon clés) |
| `POST /v1/chat` | ✅ `{messages, provider?, system?, model?, max_tokens?}` → réponse + tokens + fallback |
| `POST /v1/embed` | ✅ `{texts}` → vecteurs + provider + dim (repli hash si hors-ligne) |
| `POST /v1/rag/index` | ✅ `{namespace, id, text, meta?}` → chunking + embed + upsert |
| `POST /v1/rag/search` | ✅ `{namespace, query, k?}` → fragments proches (cosinus) |
| `POST /v1/rag/query` | ✅ `{namespace, query, k?, provider?}` → réponse augmentée + sources |
| `POST /v1/memory/{save,recall}` · `GET /v1/memory/list` | ✅ mémoire chiffrée + rappel sémantique |
| `POST /v1/knowledge/{add,search}` · `GET .../relations` | ✅ items typés + auto-linking |
| `POST /v1/agent/run` · `GET /v1/agent/capabilities` | ✅ assistant contextuel |
| `POST /v1/workflow/run` · `GET /v1/workflow/{types,runs}` | ✅ pipelines + runs persistés |
| `POST /v1/code/{analyze,debug,explain}` | ✅ modèles code locaux (Ollama) en priorité |
| `POST /v1/chat/completions` · `/v1/embeddings` · `GET /v1/models` | ✅ **format OpenAI** (Bearer/X-API-Key) |
| `GET /v1/voice/voices` · `/v1/voice/packs` (+ install/uninstall) | ✅ |
| `POST /v1/voice/{tts,stt,translate,speak}` | ⏳ 501 (V-1 → V-3) |
| `GET /v1/ecosystem/status` · `/v1/ecosystem/apps` · `/apps/{slug}` | ✅ registre Lunziko indexé (apps + fonctions) |
| `POST /v1/ecosystem/sync` · `/v1/ecosystem/search` | ✅ (re)sync du registre + recherche sémantique d'apps |
| `POST /v1/activity/{log,log-batch,search}` · `GET .../timeline` · `.../summary` | ✅ journal d'actions (detail chiffré) + recherche sémantique + résumé |
| `DELETE /v1/activity/{user_id}` | ✅ effacement (rétention / droit à l'oubli) |
| `GET /v1/neural/{status,backends}` | ✅ bibliothèques neuronales disponibles (numpy + torch/tf/jax/sklearn/transformers si installés) |
| `POST /v1/neural/{route,train}` | ✅ routeur d'intention neuronal (embeddings → classifieur) |
| `POST /v1/neural/ml/{train,predict}` · `GET .../models` | ✅ apprentissage supervisé depuis exemples (persisté) |
| `GET /v1/neural/inference` | ✅ catalogue moteurs d'inférence locaux (Ollama/llama.cpp/vLLM/LM Studio/Triton) |
| `POST /v1/data/{profile,clean,clean-text}` | ✅ profilage + nettoyage tabulaire/texte (dédup, coercition…) |
| `POST /v1/data/{prepare-rag,prepare-corpus,prepare-training}` | ✅ préparation vers RAG / corpus LLM / entraînement ML |
| `GET /v1/assistant/{app}/{scope,ui-contract,agents}` | ✅ assistant scopé à l'app + contrat UI + agents (≤5) |
| `POST /v1/assistant/{app}/{ask,team,agents}` | ✅ assistance scopée · équipe d'agents · création d'agent |
| `POST /v1/assistant/sessions` · `GET .../sessions/{id}` | ✅ sessions (interface future) |
| `WS /v1/assistant/{app}/ws` | ✅ canal temps réel pour l'interface visuelle |
| `POST /v1/handoff/{redirect,open-with,transfer}` · `GET .../file-types` | ✅ redirection inter-apps + transfert/ouverture de fichiers |
| `GET /v1/tools` · `POST /v1/tools/run` | ✅ registre d'outils + exécution directe |
| `POST /v1/agent/act` | ✅ boucle tool-calling (le modèle appelle des outils puis répond) |
| `POST /mcp` · `GET /mcp` | ✅ serveur MCP (JSON-RPC : initialize/tools.list/tools.call) |
| `POST /v1/mcp/import` | ✅ client MCP : importe les outils d'un serveur MCP externe |
| `PUT/GET /v1/appstate` · `PUT/GET /v1/profile/{user}` · `.../habits` | ✅ état applicatif live (TTL) + profil & habitudes |
| `POST /v1/context/assemble` | ✅ contexte unifié temps réel (profil+activité+état+éco, bloc system) |
| `POST /v1/feedback` · `GET .../stats` · `.../corrections` | ✅ retours utilisateur → satisfaction + few-shot |
| `POST /v1/catalog/{register,resolve}` · `GET .../schemas` | ✅ schémas de données + résolution sémantique |
| `POST /v1/automation/flows` · `.../{name}/run` · `GET .../runs` | ✅ flux de nœuds chaînant les outils (persistés) |

## Persistance & indépendance

Magasin local par défaut : `~/.lunziko/ai-engine/` (`store.db`, `vectors/`, `blobs/`, `voice/`).
Pour un déploiement couplé à Platform : `AE_STORAGE_BACKEND=postgres` + `AE_VECTOR_BACKEND=pgvector`
+ `AE_POSTGRES_DSN` (extra `postgres` : `pip install -e '.[postgres]'`). L'AI Engine crée ses tables
(`ae_kv`, `ae_vectors`) et écrit dans la base indiquée **sans modifier Platform**.

## Pile modèles (100 % permissive)

Providers LLM cloud via REST direct (clés propres à l'AI Engine) + local (llama.cpp/ONNX, phase A-1+).
Voix : Whisper (MIT) · MADLAD-400 (Apache) · Kokoro (Apache) · Piper (MIT) · OpenVoice (MIT) ·
sherpa-onnx (Apache). Modèles non-commerciaux (Coqui XTTS, NLLB) exclus de la prod.
