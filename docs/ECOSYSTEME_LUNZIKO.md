# Base de connaissance — Écosystème Lunziko (vue Lunziko AI Engine)

> ⚙️ **FICHIER AUTO-GÉNÉRÉ — NE PAS ÉDITER À LA MAIN.**
> Alimenté depuis le registre maître : `C:\Users\Joe\Desktop\Lunziko\REGISTRE_ECOSYSTEME_LUNZIKO.md`
> Version du registre : **1.3 — 15 août 2026 (LGE : spec V2 agents 23→30 planifiés + mission d'intégration transverse à toutes les apps ; bases de connaissance écosystème auto-générées depuis ce registre dans AI Engine/Graphics Engine/Design System/Platform)** · généré le 2026-08-15.
> Régénérer : `python scripts/build_ecosystem_kb.py --project "Lunziko AI Engine"` (règle §0.4 : à chaque lancement).

## Rôle de Lunziko AI Engine (extrait du registre)

- **Catégorie :** IA autonome (indépendante de Platform ; Platform = client optionnel). Objectif : **accompagner l'utilisateur** sur toutes les applications.
- **Statut :** code `lunziko-ai-engine/` (FastAPI, cœur Python, persistance enfichable locale). Modules **A-0→A-6 + A-8 + A-12 + A-13 + neural + data + assistant + handoff livrés** (16 modules). py_compile OK + tests offline (E2E écosystème : sync v1.2, 11 apps ; E2E activité : chiffrement AES-GCM ; E2E neural : routeur d'intention **HYBRIDE 12/12** vs 1/12 mots-clés bruts). Spec **Couche de Contexte Unifié** `CONTEXT_LAYER_ARCHITECTURE.md`. **+ LLM natif from scratch `lunziko-llm/`** (NumPy, RoPE/RMSNorm/GQA/SwiGLU, gradient-checké, entraîné offline) branché comme provider `lunziko`. **SOUS GIT + GITHUB (2026-08-14)** : 2 dépôts poussés — `lunziko-ai-engine/` (83 fichiers) sur **`github.com/jaisebukadilu/Lunziko_Ai_Engine`** (main @ 76a8ebd) + `lunziko-llm/` (13 fichiers) sur **`github.com/jaisebukadilu/Lunziko_LLM`** (main @ ae990f6). Les deux en synchro.
- **Fonctions exhaustives (endpoints) :**
  - **Chat / génération :** `/v1/chat` (provider manager httpx autonome + fallback).
  - **LLM natif Lunziko (paquet `lunziko-llm/`) :** architecture Transformer moderne **from scratch** (NumPy clean-room : RoPE, RMSNorm, **GQA**, SwiGLU, poids liés + micro-autograd gradient-checké + tokenizer BPE + entraînement Adam + génération). Entraîné offline (modèle jouet), branché comme **provider `lunziko`** (100 % local, sans clé). Montée en charge documentée (PyTorch/GPU, MoE, distribué). Inspiration conceptuelle des LLM ouverts Apache-2.0, aucun code copié.
  - **Embeddings & RAG :** `/v1/embed`, `/v1/rag/*` (repli hash **hors-ligne**).
  - **Mémoire :** `/v1/memory/*` (chiffrée **AES-256-GCM**).
  - **Knowledge graph :** `/v1/knowledge/*` (auto-linking).
  - **Agents :** `/v1/agent/run`.
  - **Workflows :** `/v1/workflow/*` (runs persistés).
  - **Code :** `/v1/code/*` (modèles locaux Ollama).
  - **Compatibilité :** **endpoints OpenAI-compatibles** `/v1/chat/completions`, `/v1/embeddings`, `/v1/models` (drop-in Open WebUI/LocalAI/Continue, auth Bearer/X-API-Key).
  - **Écosystème (A-12) :** `/v1/ecosystem/{sync,apps,apps/{slug},search,status}` — **ingère CE registre au démarrage** (règle §0.4 « analyse au lancement » **implémentée en code** : parseur du roster §1 → index StoragePort+VectorPort) pour **connaître toutes les apps Lunziko et leurs fonctions**, recherche sémantique d'applications (repli hash hors-ligne), **injection automatique dans le contexte des agents**. Découverte auto du fichier ou `AE_REGISTRY_PATH`.
  - **Système neuronal :** `/v1/neural/{status,backends,route,train}` — couche d'abstraction au-dessus des **bibliothèques neuronales** (backend **NumPy natif** + adaptateurs OPTIONNELS PyTorch/TensorFlow/Keras/JAX/**scikit-learn**/**Transformers**, import paresseux jamais requis pour démarrer). Capacité livrée : **routeur d'intention HYBRIDE** (classifieur neuronal embeddings-L2→softmax **fusionné** au signal lexical d'une taxonomie partagée à racines normalisées) qui améliore la réflexion de l'AgentEngine (généralise aux formulations sans mot-clé ; repli mots-clés garanti ; mesuré 12/12 vs 1/12 mots-clés bruts). Bibliothèques importées comme dépendances (licences permissives BSD/Apache), aucun code copié (⚠️ OpenNN LGPL non embarqué).
  - **Assistant d'application (intégrable à TOUTES les apps) :** `/v1/assistant/{app}/{scope,ask,team,agents,ui-contract,sessions}` + **WebSocket** `/v1/assistant/{app}/ws` — assistant **scopé à la zone de compétence** de chaque app (fonctions tirées de CE registre) qui assiste/corrige/agit dans son périmètre et **redirige hors périmètre** (garde de scope). **Jusqu'à 5 agents par application** (plafond appliqué) pour fluidifier les tâches. **Connexion prête pour une future interface visuelle** : WebSocket (événements ready/answer/error) + contrat UI (actions rapides, agents, points de connexion) + sessions persistées. → toute app Lunziko peut embarquer son assistant IA.
  - **Handoff inter-applications :** `/v1/handoff/{redirect,open-with,transfer,file-types}` — depuis une app, selon la situation : **rediriger** l'utilisateur vers l'app Lunziko compétente pour poursuivre sa tâche, **transférer** un fichier/dossier vers une autre app, ou l'**ouvrir dans l'app la plus adaptée** (résolution par type de fichier `.xlsx→DociaPub/MySheet`, `.dwg→CAD`, `.png→VidiaPub/Photo`, `.ifc→CAD/BIM`… sinon recherche sémantique dans CE registre). Produit des **actions structurées** (deep-link `lunziko://{app}/…`, executor = app hôte / HUB / Platform) exécutées par l'hôte ; intégré à l'assistant (hors périmètre → redirection attachée). **Rôle HUB (lanceur) + Platform (transport)** pour l'exécution réelle.
  - **Données (pilier « matière première ») :** `/v1/data/{profile,clean,clean-text,prepare-rag,prepare-corpus,prepare-training}` — profilage (types/nuls/distincts), nettoyage tabulaire (trim, coercition de types, valeurs manquantes, **déduplication**, lignes vides) + nettoyage de corpus texte, puis préparation vers RAG / corpus du LLM natif / table d'entraînement ML. Pur Python offline, clean-room (inspiration OpenRefine/KNIME).
  - **Apprentissage ML & inférence (pilier « algorithmes/modèles ») :** `/v1/neural/ml/{train,predict,models}` (classifieur supervisé **appris depuis exemples**, embeddings→softmax NumPy ou scikit-learn, **persisté**) ; `/v1/neural/inference` (catalogue des moteurs d'inférence locaux **Ollama/llama.cpp/vLLM/LM Studio/Triton** + provider natif `lunziko`, consommés via le Provider Manager OpenAI-compat).
  - **Activité (A-13) :** `/v1/activity/{log,log-batch,timeline,search,summary}` + `DELETE` — **journal des actions utilisateur** (les apps publient ce que fait l'utilisateur) = 1ʳᵉ brique de la **Couche de Contexte Unifié** (`CONTEXT_LAYER_ARCHITECTURE.md`, A-13→A-18) ; timeline + recherche sémantique + résumé, champ libre **chiffré** (AES-256-GCM), injecté dans le contexte des agents. **À venir : appstate (A-16), profil/RBAC consommé de Platform (A-14), assembleur de contexte (A-15), connecteurs RAG, catalogue de schémas (A-17), feedback (A-18), Action Registry (function calling).**
  - **Voix :** TTS/STT/MT — **18 packs** (code 501).
  - **Persistance :** ports SQLite/vector/blob ; **adaptateur Postgres/pgvector** (couplage optionnel Platform).
  - **SDK :** `@lunziko/ai-engine` (TS).
  - **À venir :** A-7 **MCP** (client+serveur), A-4b tool-calling, A-9 SDKs Swift/Kotlin/Dart, A-10 automatisation (nœuds, clean-room), A-11 execution agent sandboxé, V-1 TTS.
- **Expose :** raisonnement, RAG, agents, workflows, mémoire, code, voix, endpoints OpenAI/MCP. **Consomme :** **manifestes & fonctions de toutes les apps (ce registre)** pour accompagner/résoudre les tâches utilisateur.

## Toutes les applications de l'écosystème (roster §1)

| Application | Catégorie | Expose (résumé) |
|---|---|---|
| **Lunziko Platform** | socle central & **autorité de licences** de l'écosystème. | identité, licences, IA gateway, API, bus, signature, registre apps/logos |
| **Lunziko HUB** | distribution & gouvernance (app-store interne, style Creative Cloud) de l'écosystème (5 suites). | distribution, MàJ, catalogue téléchargeable, relations |
| **Lunziko AI Engine** ⭐ | IA autonome (indépendante de Platform ; Platform = client optionnel). Objectif : **accompagner l'utilisateur** sur toutes les applications. | raisonnement, RAG, agents, workflows, mémoire, code, voix, endpoints OpenAI/MCP |
| **Lunziko Graphics Engine (LGE)** | moteur graphique / rendu (JSON-RPC, architecture à **22 agents**). | rendus haute qualité (graphiques/visuels), imaging, vector, PDF, CAD/BIM/sketch. **Exposera (roadmap V2) :** NURBS, GPUCompute, ClashDetection, RuleChecker, AI-Render, Physics, MaterialCatalog, SceneOptimizer |
| **Lunziko Design System (LDS)** | plateforme de conception unifiée de **toute** la suite Lunziko. | tokens & composants (build-time, aucun appel runtime) |
| **Lunziko One** | suite **ERP** métier modulaire IA-native (FR + CH). Adossée à Platform. | données métier + événements (`finance.entry.posted`, `payroll.run.closed`, `sales.order.confirmed`…) via **Lunziko Data API** |
| **Lunziko BI** | **Business Intelligence / Data Analytics / Reporting** — couche Data/Analytics commune de l'écosystème. | analytics, dashboards, graphiques liés, API BI, embedding |
| **DociaPub (Lunziko DociaPub)** | suite **documentaire / bureautique** (cible macOS + Windows, moteur OOXML/ODF ; legacy MyOfficeSuite Swift 43k LOC comme référence). | génération/édition/rendu de documents ; MySheet/MyData = sources ; MyWord/MySlides/MyMail/MyPublish = cibles |
| **Lunziko VidiaPub** | suite **créative** (macOS + Windows ; nom interne « Lunziko »). | création graphique/vidéo/audio/PDF/logo |
| **Lunziko CAD** | **CAO / DAO** (Architecture + CAO mécanique). | modèles CAO/DAO |
| **Lunziko Yekoli** | plateforme d'**apprentissage des langues**. | contenus & progression d'apprentissage |

## Détail des fonctions par application (extrait du registre)

### Lunziko Platform

- **Catégorie :** socle central & **autorité de licences** de l'écosystème.
- **Statut :** monorepo bun+turbo déployé (Vercel) — `apps/web` (Next.js 14, `lunziko-platform.vercel.app`) + `server/api` (Hono, `lunziko-api.vercel.app`) + `packages/sdk-typescript` (12 modules) + `server/gaming-engine` (C++) + microservices 3D-python / piper-tts. Supabase `xtvfkyfjsnrzmtgnzicc`. Chantier licences hybride (branche `feature/licensing-authority`).
- **Fonctions exhaustives :**
  - **Identité & accès :** SSO/Auth **OIDC/OAuth2**, JWT, **RBAC**, **multi-tenant** (multi-sociétés), gestion utilisateurs/rôles/scopes.
  - **Licences & entitlements (autorité unique) :** émission, révocation, **JWT de licence signé** vérifiable hors-ligne, entitlements par app/module/**service** (sdk, agent_deployment), **provisionnement** (membres entreprise, bénéficiaires particuliers), **allocation par app**, **partage famille**, **download-gating** (piloté vers HUB), consoles **Staff/Support**, admin provisioning.
  - **Facturation :** Subscription, Billing, paliers d'abonnement.
  - **IA :** **Gateway IA** multi-providers (claude/openai/gemini/mistral/deepseek + **auto-fallback**), **ThinkingEngine**, **SkillsRegistry**, **PersonaManager**.
  - **API & événementiel :** **API Gateway** REST/GraphQL, **bus de messages** (backbone interne, ordre/rejeu/back-pressure) + **webhooks** (façade externe).
  - **3D & jeu :** **3D Pipeline** (Blender/Unity/Unreal/Maya + GPU OptiX/CUDA/Arc), **Gaming Engine v2** (6 agents IA).
  - **Transverse :** sécurité (chiffrement transit/repos, audit/traçabilité), notifications, reporting, moteur de recherche global, workflows configurables, **service « Trust & Signature »** (signature qualifiée eIDAS/ZertES, horodatage, coffre-fort), **registre des apps & logos**.
- **Expose :** identité, licences, IA gateway, API, bus, signature, registre apps/logos. **Consomme :** — (socle ; agrège les manifestes de toutes les apps).

### Lunziko HUB

- **Catégorie :** distribution & gouvernance (app-store interne, style Creative Cloud) de l'écosystème (5 suites).
- **Statut :** CDC v2.0 + charte « Dark Studio » (#131313 / **#007AFF**, Inter+JetBrains Mono) + socle UI `client/` (Vite+React+TS+Tailwind), Dashboard Unified Manager v2.0. Reco stack Tauri/Rust + PostgreSQL Francfort.
- **Fonctions exhaustives :**
  - **Catalogue :** liste des applications **téléchargeables**, fiches produit, logos, catégories.
  - **Distribution :** téléchargement, **installation**, **mise à jour** des apps & modules ; **canaux de release** (stable/beta/…) ; delta updates.
  - **Gouvernance des droits :** **download-gating** selon licences (activation/désactivation d'apps & de modules), **y compris hors-ligne** ; se réfère **en priorité à Platform** (licences consommées hors-ligne).
  - **Relations :** **affichage des relations** entre apps (Applications compatibles + Services : Platform/AI/Data Layer).
  - **Lancement :** lanceur des applications de l'écosystème (Unified Manager).
- **Expose :** distribution, MàJ, catalogue téléchargeable, relations. **Consomme :** **Platform en priorité** (licences), ce registre.

### Lunziko AI Engine

- **Catégorie :** IA autonome (indépendante de Platform ; Platform = client optionnel). Objectif : **accompagner l'utilisateur** sur toutes les applications.
- **Statut :** code `lunziko-ai-engine/` (FastAPI, cœur Python, persistance enfichable locale). Modules **A-0→A-6 + A-8 + A-12 + A-13 + neural + data + assistant + handoff livrés** (16 modules). py_compile OK + tests offline (E2E écosystème : sync v1.2, 11 apps ; E2E activité : chiffrement AES-GCM ; E2E neural : routeur d'intention **HYBRIDE 12/12** vs 1/12 mots-clés bruts). Spec **Couche de Contexte Unifié** `CONTEXT_LAYER_ARCHITECTURE.md`. **+ LLM natif from scratch `lunziko-llm/`** (NumPy, RoPE/RMSNorm/GQA/SwiGLU, gradient-checké, entraîné offline) branché comme provider `lunziko`. **SOUS GIT + GITHUB (2026-08-14)** : 2 dépôts poussés — `lunziko-ai-engine/` (83 fichiers) sur **`github.com/jaisebukadilu/Lunziko_Ai_Engine`** (main @ 76a8ebd) + `lunziko-llm/` (13 fichiers) sur **`github.com/jaisebukadilu/Lunziko_LLM`** (main @ ae990f6). Les deux en synchro.
- **Fonctions exhaustives (endpoints) :**
  - **Chat / génération :** `/v1/chat` (provider manager httpx autonome + fallback).
  - **LLM natif Lunziko (paquet `lunziko-llm/`) :** architecture Transformer moderne **from scratch** (NumPy clean-room : RoPE, RMSNorm, **GQA**, SwiGLU, poids liés + micro-autograd gradient-checké + tokenizer BPE + entraînement Adam + génération). Entraîné offline (modèle jouet), branché comme **provider `lunziko`** (100 % local, sans clé). Montée en charge documentée (PyTorch/GPU, MoE, distribué). Inspiration conceptuelle des LLM ouverts Apache-2.0, aucun code copié.
  - **Embeddings & RAG :** `/v1/embed`, `/v1/rag/*` (repli hash **hors-ligne**).
  - **Mémoire :** `/v1/memory/*` (chiffrée **AES-256-GCM**).
  - **Knowledge graph :** `/v1/knowledge/*` (auto-linking).
  - **Agents :** `/v1/agent/run`.
  - **Workflows :** `/v1/workflow/*` (runs persistés).
  - **Code :** `/v1/code/*` (modèles locaux Ollama).
  - **Compatibilité :** **endpoints OpenAI-compatibles** `/v1/chat/completions`, `/v1/embeddings`, `/v1/models` (drop-in Open WebUI/LocalAI/Continue, auth Bearer/X-API-Key).
  - **Écosystème (A-12) :** `/v1/ecosystem/{sync,apps,apps/{slug},search,status}` — **ingère CE registre au démarrage** (règle §0.4 « analyse au lancement » **implémentée en code** : parseur du roster §1 → index StoragePort+VectorPort) pour **connaître toutes les apps Lunziko et leurs fonctions**, recherche sémantique d'applications (repli hash hors-ligne), **injection automatique dans le contexte des agents**. Découverte auto du fichier ou `AE_REGISTRY_PATH`.
  - **Système neuronal :** `/v1/neural/{status,backends,route,train}` — couche d'abstraction au-dessus des **bibliothèques neuronales** (backend **NumPy natif** + adaptateurs OPTIONNELS PyTorch/TensorFlow/Keras/JAX/**scikit-learn**/**Transformers**, import paresseux jamais requis pour démarrer). Capacité livrée : **routeur d'intention HYBRIDE** (classifieur neuronal embeddings-L2→softmax **fusionné** au signal lexical d'une taxonomie partagée à racines normalisées) qui améliore la réflexion de l'AgentEngine (généralise aux formulations sans mot-clé ; repli mots-clés garanti ; mesuré 12/12 vs 1/12 mots-clés bruts). Bibliothèques importées comme dépendances (licences permissives BSD/Apache), aucun code copié (⚠️ OpenNN LGPL non embarqué).
  - **Assistant d'application (intégrable à TOUTES les apps) :** `/v1/assistant/{app}/{scope,ask,team,agents,ui-contract,sessions}` + **WebSocket** `/v1/assistant/{app}/ws` — assistant **scopé à la zone de compétence** de chaque app (fonctions tirées de CE registre) qui assiste/corrige/agit dans son périmètre et **redirige hors périmètre** (garde de scope). **Jusqu'à 5 agents par application** (plafond appliqué) pour fluidifier les tâches. **Connexion prête pour une future interface visuelle** : WebSocket (événements ready/answer/error) + contrat UI (actions rapides, agents, points de connexion) + sessions persistées. → toute app Lunziko peut embarquer son assistant IA.
  - **Handoff inter-applications :** `/v1/handoff/{redirect,open-with,transfer,file-types}` — depuis une app, selon la situation : **rediriger** l'utilisateur vers l'app Lunziko compétente pour poursuivre sa tâche, **transférer** un fichier/dossier vers une autre app, ou l'**ouvrir dans l'app la plus adaptée** (résolution par type de fichier `.xlsx→DociaPub/MySheet`, `.dwg→CAD`, `.png→VidiaPub/Photo`, `.ifc→CAD/BIM`… sinon recherche sémantique dans CE registre). Produit des **actions structurées** (deep-link `lunziko://{app}/…`, executor = app hôte / HUB / Platform) exécutées par l'hôte ; intégré à l'assistant (hors périmètre → redirection attachée). **Rôle HUB (lanceur) + Platform (transport)** pour l'exécution réelle.
  - **Données (pilier « matière première ») :** `/v1/data/{profile,clean,clean-text,prepare-rag,prepare-corpus,prepare-training}` — profilage (types/nuls/distincts), nettoyage tabulaire (trim, coercition de types, valeurs manquantes, **déduplication**, lignes vides) + nettoyage de corpus texte, puis préparation vers RAG / corpus du LLM natif / table d'entraînement ML. Pur Python offline, clean-room (inspiration OpenRefine/KNIME).
  - **Apprentissage ML & inférence (pilier « algorithmes/modèles ») :** `/v1/neural/ml/{train,predict,models}` (classifieur supervisé **appris depuis exemples**, embeddings→softmax NumPy ou scikit-learn, **persisté**) ; `/v1/neural/inference` (catalogue des moteurs d'inférence locaux **Ollama/llama.cpp/vLLM/LM Studio/Triton** + provider natif `lunziko`, consommés via le Provider Manager OpenAI-compat).
  - **Activité (A-13) :** `/v1/activity/{log,log-batch,timeline,search,summary}` + `DELETE` — **journal des actions utilisateur** (les apps publient ce que fait l'utilisateur) = 1ʳᵉ brique de la **Couche de Contexte Unifié** (`CONTEXT_LAYER_ARCHITECTURE.md`, A-13→A-18) ; timeline + recherche sémantique + résumé, champ libre **chiffré** (AES-256-GCM), injecté dans le contexte des agents. **À venir : appstate (A-16), profil/RBAC consommé de Platform (A-14), assembleur de contexte (A-15), connecteurs RAG, catalogue de schémas (A-17), feedback (A-18), Action Registry (function calling).**
  - **Voix :** TTS/STT/MT — **18 packs** (code 501).
  - **Persistance :** ports SQLite/vector/blob ; **adaptateur Postgres/pgvector** (couplage optionnel Platform).
  - **SDK :** `@lunziko/ai-engine` (TS).
  - **À venir :** A-7 **MCP** (client+serveur), A-4b tool-calling, A-9 SDKs Swift/Kotlin/Dart, A-10 automatisation (nœuds, clean-room), A-11 execution agent sandboxé, V-1 TTS.
- **Expose :** raisonnement, RAG, agents, workflows, mémoire, code, voix, endpoints OpenAI/MCP. **Consomme :** **manifestes & fonctions de toutes les apps (ce registre)** pour accompagner/résoudre les tâches utilisateur.

### Lunziko Graphics Engine (LGE)

- **Catégorie :** moteur graphique / rendu (JSON-RPC, architecture à **22 agents**).
- **Mission d'intégration (transverse) :** le LGE doit pouvoir **s'intégrer à TOUTES les applications Lunziko** (One, BI, DociaPub, VidiaPub, CAD, Yekoli, Platform, HUB, AI Engine, Design System) pour **les faire fonctionner correctement** (fournir rendus/graphiques/géométrie/PDF/CAD-BIM là où elles en ont besoin), **les améliorer** et **leur apporter de nouvelles fonctionnalités** graphiques. Intégration par **contrats d'API versionnés** (JSON-RPC/REST), jamais de couplage de code ; chaque app consomme les capacités du LGE via ce registre.
- **Intégration AI Engine (consommateur) :** le LGE doit pouvoir **appeler, faire fonctionner et utiliser les fonctionnalités de [[Lunziko AI Engine]]** — voire **embarquer l'AI Engine** — afin d'apporter les capacités IA à une application qu'il sert. Cas d'usage : agent **AI-Render** (27) qui délègue génération de vues / rendu photoréaliste / auto-fix de sketches à l'AI Engine ; assistance IA sur les rendus/scènes ; NL→opérations graphiques. **Accès via les endpoints AI Engine** (autonomes, OpenAI-compat `/v1/chat/completions`+`/v1/embeddings`, `/v1/agent/run`, `/v1/rag/*`, provider `lunziko` local) ou en **embarquant** le paquet `lunziko-ai-engine`. Découplé (repli si AI Engine indisponible), clean-room, licences/identité restant à Platform.
- **Statut :** master=origin, **1005 tests ✅**. Codes d'erreur JSON-RPC **-32000 → -32022**. Seul dossier à modifier pour le LGE.
- **Fonctions exhaustives (agents & capacités) :**
  - **Imaging** (Pillow+numpy, `IMAGING_ERROR=-32012`).
  - **Asset** (trimesh, **scènes multi-objets**, `ASSET_ERROR=-32013`).
  - **Vector** (pur Python) — 10ᵉ agent.
  - **PDF** (génération, pur Python) — 11ᵉ agent.
  - **CAD** (C1, OCCT).
  - **BIM** (C3, IfcOpenShell).
  - **Sketch** paramétrique (CAO : contraintes 2D Levenberg-Marquardt numpy + **extrude/revolve** OCCT, `SKETCH_ERROR=-32022`) — 22ᵉ agent.
  - **Workflow** (é37/é38).
  - **Phase E — DAO/VR :** Integrity, Accel, VR.
  - **Phase F — moteur de jeu :** Cache, Shader, Catalog.
  - **Registre moteurs :** vision ~40 moteurs (`docs/SPECIFICATION_LGE.md`, `MOTEURS_REFERENCE.md`, `manager/engines.py`).
  - **Agents planifiés (spec V2, `docs/SPECIFICATION_LGE_V2_AGENTS_23-30.md`, NON codés) :** NURBS (23, `NURBS_ERROR=-32023`), GPUCompute (24, `GPU_ERROR=-32024`), ClashDetection BIM (25, `CLASH_ERROR=-32025`), RuleChecker IFC (26, `RULECHECK_ERROR=-32026`), AI-Render (27, `AIRENDER_ERROR=-32027`), Physics (28, `PHYSICS_ERROR=-32028`), MaterialCatalog (29, `MATERIAL_ERROR=-32029`), SceneOptimizer (30, `SCENE_ERROR=-32030`). Codes réservés -32023→-32030.
  - **Roadmap :** Phase D = GPUCompute/Physics/AI-Render (rendu/physics pybullet/GPU/AI onnxruntime) · Phase E+ = ClashDetection/RuleChecker (+ extraction géométrie ifcopenshell.geom) · Phase F+ = MaterialCatalog/SceneOptimizer · NURBS = extension Geometry/CAD (OCCT).
- **Expose :** rendus haute qualité (graphiques/visuels), imaging, vector, PDF, CAD/BIM/sketch. **Exposera (roadmap V2) :** NURBS, GPUCompute, ClashDetection, RuleChecker, AI-Render, Physics, MaterialCatalog, SceneOptimizer. **Consomme :** spécifications de rendu émises par les apps (ce registre pour connaître leurs besoins) ; **fonctionnalités de l'AI Engine** (chat/agents/RAG/embeddings/provider `lunziko`, appelé ou embarqué) pour les capacités IA-graphiques.

### Lunziko Design System (LDS)

- **Catégorie :** plateforme de conception unifiée de **toute** la suite Lunziko.
- **Statut :** monorepo pnpm+Turborepo+Changesets+TS strict (`github.com/jaisebukadilu/lunziko-design-system`, privé). **Phases 0→7 faites** ; build 9/9 · typecheck 13/13 · test 13/13.
- **Fonctions exhaustives :**
  - **Tokens :** `@lunziko/tokens` (DTCG 3 étages → Style Dictionary → **CSS / TS / Swift / Kotlin / Dart / XAML WinUI+WPF / GTK CSS / gpu JSON**) × thèmes **dark / light / high-contrast**.
  - **Composants (19+ React + parité Web Components + Flutter partiel) :** Button, TextInput, Checkbox, Radio, Switch, Select, Dialog, Badge, Alert, Spinner, Tooltip, BrandHero, Divider, Card, Progress, Breadcrumb, Logo, BrandFooter (+ batch2 à venir : Tabs, Menu, Table).
  - **Densité :** comfortable / compact (`[data-density]`).
  - **Marques :** **6 chartes de marque exclusives** (`[data-brand][data-theme]`) : vidiapub, cad, hub, one, yekoli, dociapub (re-résolution des tokens composant).
  - **Logos :** règle des logos (logo société Lunziko obligatoire + services connectés même ligne ; le LDS ne bundle pas les logos d'autrui) — manifeste + BrandFooter.
  - **Doc & CI :** site `@lunziko/docs` (Vite+React : Design Language/Foundations/Tokens explorer/Composants, bascules thème+densité) ; CI GitHub Actions ; Storybook, Vitest+axe, Playwright.
- **Expose :** tokens & composants (build-time, aucun appel runtime). **Consomme :** chartes/marques & besoins UI des apps (ce registre).

### Lunziko One

- **Catégorie :** suite **ERP** métier modulaire IA-native (FR + CH). Adossée à Platform.
- **Statut :** CDG v4.0, charte « Ether » (glassmorphism dark, gradient **#2E7CFF → #9D50FF**, Inter), ~42 maquettes Stitch (définitives), interface web `apps/one-web/` (Next.js 14) **démarrée** (Connexion, Dashboard global, Finance compta/overview + Facturation). Persistance multi-SGBD (PostgreSQL/MySQL/MariaDB via ORM). Clean-room inspiré MS D365 BC.
- **Fonctions exhaustives (12 modules, V1→V5) :**
  - **Finance :** CA, revenus, dépenses, charges, bénéfices/pertes, trésorerie, comptes, écritures, budgets, prévisions, paiements, factures (FR : PDP/PPF ; CH : QR-facture), fournisseurs, clients, dimensions analytiques multi-axes, centres de coûts, gestion devises & réévaluation, rapprochement bancaire.
  - **Comptabilité :** journaux, comptes, mouvements, périodes, balances, résultats, bilan, compte de résultat, clôtures.
  - **Ventes (Sales) :** devis→commande→livraison→facture, produits, clients, commerciaux, régions, marges, remises & tarifs échelonnés, retours/avoirs.
  - **Achats (Purchase) :** commandes fournisseurs, fournisseurs, achats, prix, délais, coûts, workflows d'approbation.
  - **Stocks (Inventory) :** stocks, mouvements, entrées/sorties, inventaires, ruptures, rotations, valorisation (FIFO/moyenne pondérée), emplacements/entrepôts, réappro & points de commande, traçabilité lot/série.
  - **RH :** effectifs, départements, postes, contrats, ancienneté, absences, congés, masse salariale, recrutement, turnover (données sensibles soumises à la sécurité Platform).
  - **Payroll (Paie).**
  - **CRM** (relation client), **Projects** (jobs/tâches, WIP, rentabilité), **Manufacturing/Service** (roadmap : BOM, ordres de production, contrats de service).
  - **Analytics :** entrée **« Analytics » → ouvre Lunziko BI** ; **module client léger embarquant les dashboards BI** ; **deep-linking** (ex. facture → analyser dans BI).
  - **Marketplace (V5).**
  - **Transverse :** e-documents (facturation électronique), subscription billing, workflows d'approbation configurables.
- **Expose :** données métier + événements (`finance.entry.posted`, `payroll.run.closed`, `sales.order.confirmed`…) via **Lunziko Data API**. **Consomme :** BI, DociaPub, AI Engine, Graphics Engine, Platform (auth/licences/signature), HUB.

### Lunziko BI

- **Catégorie :** **Business Intelligence / Data Analytics / Reporting** — couche Data/Analytics commune de l'écosystème.
- **Statut :** CDC v1.1, charte « Lunziko BI Design System » (dark Command Center, Hanken/Inter/JetBrains, primary **#0062FF**), 28 maquettes Stitch (21 desktop + 7 mobile). Design+spec. Fichiers `INTEROPERABILITE_ECOSYSTEME.md` + `MEMOIRE_PROJET.md` présents.
- **Fonctions exhaustives :**
  - **Données & modélisation :** connexion de sources (fichiers, **SQL**), import **XLSX/CSV/ODS/JSON**/tabulaires Lunziko, **datasets**, **data models**, **mesures**, catalogue de données certifiées.
  - **Restitution :** **rapports** (éditeur de rapports), **dashboards** (dashboard principal / exécutif), **KPIs**, data explorer, **graphiques dynamiques embarquables** (liés à la source).
  - **Connecteurs natifs :** **Lunziko One Connector** (découverte auto selon droits), **MySheet Connector**, **MyData Connector**, connecteur écosystème.
  - **Data Layer / Data API :** `/api/v1/{data,datasets,sources,tables,schema,analytics}` ; datasets partagés (Single Source of Truth) ; synchronisation temps réel / quasi temps réel / planifiée / manuelle.
  - **Dashboards prêts à l'emploi :** Direction, Finance, Commercial, RH, Stock.
  - **IA :** **AI insights** / smart insights, **assistant vocal IA**, NL→requête, résumés exécutifs, prévisions, **orchestrateur IA écosystème**, copilot cross-app, automatisation des rapports financiers.
  - **Simulation :** **what-if scenarios**, simulation de scénarios stratégiques.
  - **Gouvernance & sécurité :** tableau de bord de gouvernance, souveraineté des données, **lignage & traçabilité** des données, sécurité **Lunziko Data Layer**, **héritage des droits de la source** (BI ≤ droits source).
  - **Intégrations DociaPub :** intégration MySheet, éditeur MyWord intégré, synthèse stratégique MyWord, générateur MySlides, publication MyPublish, partage via MyMail.
  - **Mobile :** dashboard exécutif, alertes intelligentes, collaboration temps réel, exploration **AR**, lignage des données, **monitoring IoT/edge**, assistant vocal.
  - **Export/partage :** PDF, CSV, MySheet, MyWord, MySlides, MyMail, MyPublish.
  - **Licences :** paliers **Free** (local) / **Professional** (One) / **Business** (One+DociaPub) / **Enterprise** (API, embedding, data governance).
- **Expose :** analytics, dashboards, graphiques liés, API BI, embedding. **Consomme :** One, DociaPub, Data Layer, AI Engine, Graphics Engine, Platform, HUB.

### DociaPub (Lunziko DociaPub)

- **Catégorie :** suite **documentaire / bureautique** (cible macOS + Windows, moteur OOXML/ODF ; legacy MyOfficeSuite Swift 43k LOC comme référence).
- **Statut :** phases 1 & 2 livrées (cartographie + **moteur documentaire DDM** hybride, filtres OOXML/ODF, layout→RenderPort, **8 ports** définis) ; socle monorepo TS+Tauri (app pilote MyWord). Design, rien codé.
- **Fonctions exhaustives (7 applications de la suite) :**
  - **MyWord** — traitement de texte (rédaction, styles, tableaux, graphiques liés BI, export PDF/DDM, génération de rapports analytiques).
  - **MySheet** — tableur (feuilles, plages, tri/filtre/transformation, formats XLSX/CSV/ODS/JSON, **« Analyser avec Lunziko BI »**, export/import BI).
  - **MySlides** — présentations (slides, graphiques BI liés, génération auto de présentations IA).
  - **MyMail** — email (envoi de rapports : lien sécurisé / PDF / image / résumé IA).
  - **MyNotes** — notes (analyses, observations, hypothèses, conclusions ; IA → notes structurées).
  - **MyData** — base de données structurée (source de datasets pour BI).
  - **MyPublish** — PAO / publication professionnelle (rapports annuels/financiers/d'activité, brochures, documents institutionnels).
  - **Transverse :** rendu web/canvas façon ONLYOFFICE, moteur doc façon LibreOffice/AOO, coffre-fort, signature via service Platform.
- **Expose :** génération/édition/rendu de documents ; MySheet/MyData = sources ; MyWord/MySlides/MyMail/MyPublish = cibles. **Consomme :** BI, AI Engine, Graphics Engine, Platform (auth/signature), HUB.

### Lunziko VidiaPub

- **Catégorie :** suite **créative** (macOS + Windows ; nom interne « Lunziko »).
- **Statut :** macOS v2.0 abouti (**148 fichiers Swift**) ; Windows WinUI 3 = squelette (~5 %). Charte « VidiaPub Core » (Dark Studio, Inter/JetBrains, Blue-600 #007AFF). Socle préparé pour greffes AI/Design/Graphics/Platform.
- **Fonctions exhaustives (6 modules) :**
  - **Publisher** — PAO / mise en page.
  - **Photo** — retouche & édition d'images.
  - **PDF** — édition/manipulation PDF.
  - **Logo** — création de logos (→ orientation Design/violet).
  - **Vidéo** — montage/édition vidéo.
  - **Audio** — édition audio (6ᵉ module).
  - **Transverse :** shell **Metal**, **SpaceMouseDriver**, contrats « partagés, impl. natives » (Swift/C#), tokens design générés.
- **Expose :** création graphique/vidéo/audio/PDF/logo. **Consomme :** AI Engine, Design System, Graphics Engine, Platform, HUB.

### Lunziko CAD

- **Catégorie :** **CAO / DAO** (Architecture + CAO mécanique).
- **Statut :** monorepo pnpm/Turborepo + TS + Tauri/Rust + React + three.js + opencascade.js (8 phases). Phase 0 (socle web) faite & validée ; charte « Technical Precision » (fond #071424, accent **#1e6fe0**, AI cyan **#00F5FF**, argent #C0C0C0). Phase 1 en pause (statut LGE à trancher).
- **Fonctions exhaustives :** modélisation 2D/3D **paramétrique**, **contraintes**, **extrude/revolve**, rendu **three.js**, **app shell 3 panneaux**, architecture + mécanique ; consomme potentiellement le **Graphics Engine** (moteur sketch/CAD/BIM) ou un LGE Python séparé (décision en attente).
- **Expose :** modèles CAO/DAO. **Consomme :** Graphics Engine, AI Engine, Design System, Platform, HUB.

### Lunziko Yekoli

- **Catégorie :** plateforme d'**apprentissage des langues**.
- **Statut :** Next.js 14 + Supabase + Vercel. **Phase 0 livrée** (squelette, auth, migrations RLS West EU, thème Yekoli, Freemium, domaine `yekoli.lunziko.app`). GitHub `jaisebukadilu/Lunziko-Yekoli`.
- **Fonctions exhaustives :** apprentissage des langues, **Language Engine hexagonal (FSRS)** (répétition espacée), leçons/progression, mobile **RN/Expo**, corpus (**lingála**), modèle **Freemium**. MVP Web EN+FR à venir (Phase 1).
- **Expose :** contenus & progression d'apprentissage. **Consomme :** AI Engine, Design System, Platform, HUB.

## Suites et applications (§1.D)

### 1.D — Suites d'applications et leurs applications/modules

| Suite / Produit | Type | Applications / modules constitutifs |
|---|---|---|
| **DociaPub** | Suite documentaire (7 apps) | MyWord · MySheet · MySlides · MyMail · MyNotes · MyData · MyPublish |
| **Lunziko VidiaPub** | Suite créative (6 modules) | Publisher · Photo · PDF · Logo · Vidéo · Audio |
| **Lunziko One** | Suite ERP (12 modules, V1→V5) | Finance · Comptabilité · Ventes · Achats · Stocks · RH · Payroll · CRM · Projects · Manufacturing/Service · Analytics (client léger BI) · Marketplace |
| **Lunziko BI** | Application unique (multi-vues) | 21 vues desktop + 7 vues mobile (dashboards, rapports, gouvernance, lignage, simulation, IA, mobile AR/IoT/vocal…) |
| **Lunziko CAD** | Application unique | CAO Architecture + CAO mécanique (2D/3D paramétrique) |
| **Lunziko Yekoli** | Application unique | Web + mobile RN/Expo (Language Engine FSRS) |
| **Lunziko Platform** | Socle / services (12 modules SDK) | Identity · Licensing · Subscription · Billing · AI Gateway · API · Security · Bus/Events · Trust&Signature · 3D Pipeline · Gaming Engine · Registre apps/logos |
| **Lunziko HUB** | Socle / distribution | Catalogue · Distribution/MàJ · Download-gating · Relations · Lanceur (Unified Manager) |
| **Lunziko AI Engine** | Socle / IA (16 modules) | chat · embed · rag · memory · knowledge · agent · workflow · code · OpenAI-compat · **ecosystem** · **activity** · **neural** (routeur+ML+inférence) · **data** · **assistant** (scopé/app + agents≤5 + WebSocket UI) · **handoff** (redirection/transfert/ouverture inter-apps) · voice |
| **Lunziko Graphics Engine** | Socle / rendu (22 agents) | imaging · asset · vector · pdf · cad · bim · sketch · workflow · integrity · accel · vr · cache · shader · catalog … |
| **Lunziko Design System** | Socle / UI | tokens (8 cibles) · 19+ composants · 6 marques · densités · docs · CI |

> **Hors périmètre écosystème produit :** *ARC Église* (site client Next.js/Supabase), *MyOfficeSuite* (legacy Swift → devenu **DociaPub**), *LunzikoEngine/LCPEngine* (moteurs SPM macOS bas niveau). Non distribués via HUB en tant que produits Lunziko commerciaux.

## Règles de gouvernance (§0)

## 0. Règles de gouvernance (OBLIGATOIRES)

1. **Source de vérité = Lunziko Platform** pour les identités, licences, abonnements et **logos** des applications. **HUB se réfère en priorité à Platform**.
2. **Publication obligatoire.** Toute application Lunziko **doit communiquer ses informations** (manifeste : nom, catégorie, statut, fonctionnalités, ce qu'elle expose/consomme, logo, charte) aux **5 agrégateurs** de l'écosystème :
   - **Lunziko AI Engine** — pour raisonner sur l'écosystème et accompagner/résoudre les tâches de l'utilisateur ;
   - **Lunziko Design System** — pour disposer des bonnes informations d'UI/marque ;
   - **Lunziko Graphics Engine** — pour rendre au mieux (rendus, graphiques, visuels) ;
   - **Lunziko HUB** — pour tenir à jour la liste des applications téléchargeables ;
   - **Lunziko Platform** — pour la liste complète des applications, leurs logos, licences et services.
3. **Liste complète.** HUB, Platform, AI Engine et Graphics Engine **doivent posséder la liste complète** de toutes les applications (existantes **et à venir**) et de leurs fonctionnalités.
4. **Analyse au lancement (OBLIGATOIRE).** À **chaque lancement** des projets **HUB, Platform, AI Engine et Graphics Engine**, ce fichier **doit être analysé** pour **mettre à jour la mémoire** de ces projets.
5. **Traçabilité des ajouts.** À **chaque ajout d'une fonctionnalité** (ou d'une application) dans l'écosystème, l'entrée correspondante de ce registre **doit être mise à jour** (et consignée en mémoire projet).
6. **Finalité.** Rendre l'IA plus performante et capable de résoudre / accompagner l'utilisateur ; permettre à Graphics de donner son meilleur ; à Platform d'avoir la liste complète des apps + logos ; à HUB d'être à jour sur ses téléchargements ; au Design System d'avoir les bonnes informations.

> **Convention logo :** chaque projet contient un dossier `_logo/` (ou `_Logo/`). Le logo **société Lunziko** + le logo **produit** sont obligatoires (bas d'accueil) ; les logos des services connectés se greffent sur la même ligne. Platform agrège les logos de toutes les apps.

## Matrice de communication obligatoire (§2)

## 2. Matrice de communication obligatoire

> **Toutes les applications** doivent obligatoirement communiquer leurs informations à : **AI Engine · Design System · Graphics Engine · HUB · Platform.**

| Application ↓ / Agrégateur → | AI Engine | Design System | Graphics Engine | HUB | Platform |
|---|:---:|:---:|:---:|:---:|:---:|
| Lunziko One | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lunziko BI | ✓ | ✓ | ✓ | ✓ | ✓ |
| DociaPub | ✓ | ✓ | ✓ | ✓ | ✓ |
| VidiaPub | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lunziko CAD | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lunziko Yekoli | ✓ | ✓ | ✓ | ✓ | ✓ |
| *(les agrégateurs se publient aussi mutuellement leurs capacités)* | ✓ | ✓ | ✓ | ✓ | ✓ |

**Informations communiquées (manifeste minimal par app) :** nom · catégorie · statut · **liste des fonctionnalités** · ce qu'elle **expose** / **consomme** · **logo** · charte/marque · version d'API (SemVer).
