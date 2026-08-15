# Lunziko AI Engine — Couche de Contexte Unifié (A-13 → A-18)

> **Objet.** Donner à l'AI Engine un **contexte unifié et temps réel** sur les données de
> l'écosystème (profil utilisateur, historique d'actions, état applicatif, bases de
> connaissances, schémas de données) **et** la capacité d'**agir** (function calling) puis de
> **s'améliorer** via le feedback — pour passer d'une IA qui *génère du texte* à une IA
> d'**application** qui *accompagne et exécute*.
>
> **Statut du document : SPEC (design). L'implémentation se fait phase par phase, avec arrêt
> et validation.** A-13 (Activity & Events) est livré comme première brique concrète (voir §6).

---

## 0. Principes directeurs (non négociables)

1. **Indépendance.** Tout fonctionne en local par défaut (StoragePort/VectorPort/BlobPort,
   repli embeddings hash). Aucune dépendance dure à Platform.
2. **Frontière Platform (capital).** L'**identité, les rôles, les permissions (RBAC), les
   licences** sont l'autorité de **Lunziko Platform** (cf. registre §0.1/§3). L'AI Engine **ne
   recode PAS un Keycloak/Authelia** : il **consomme** ces informations (quand Platform est
   branché) et n'en garde qu'un **cache de profil comportemental**. On n'importe jamais de
   fournisseur d'identité.
3. **Clean-room total.** Les dépôts cités en annexe servent d'**inspiration conceptuelle
   uniquement**. **Aucune ligne de code tierce n'est copiée** (cf. [[feedback_clean_room_no_code_copy]]).
   Voir l'analyse de licences §7 — plusieurs sources sont **AGPL / BSL / fair-code** (contamination
   si copie).
4. **Confidentialité par conception.** Historique d'actions, état applicatif, localisation =
   **données sensibles**. Champs libres **chiffrés** (réutilise le cipher AES-256-GCM de la
   mémoire), **rétention/TTL** paramétrable, **consentement** et **minimisation**, héritage des
   droits de la source.
5. **Sur les ports existants.** On étend l'architecture hexagonale actuelle ; on ajoute des
   modules, pas une nouvelle pile.

---

## 1. Cartographie besoin → architecture

Le brief se décompose en **3 axes** ; chacun se mappe sur des modules AI Engine (existants ou nouveaux).

| # | Besoin (brief) | Réponse AI Engine | Statut |
|---|---|---|---|
| 1 | **Historique des actions** | **A-13 `activity`** — journal d'événements append-only + timeline + résumé | ✅ livré (§6) |
| 1 | **Préférences / profil / rôles / permissions** | **A-14 `profile`** — cache profil + préférences + habitudes dérivées ; **RBAC = Platform (consommé)** | 🔜 spec |
| 1 | **Contexte temporel & spatial** | **A-15 `context` (assembler)** — fuseau, moment, locale, localisation optionnelle | 🔜 spec |
| 2 | **État applicatif en direct** | **A-16 `appstate`** — canal éphémère (écran courant, brouillon de formulaire, dernière erreur), TTL | 🔜 spec |
| 2 | **Bases de connaissances unifiées (RAG)** | **Extension A-2 `rag`** — connecteurs (docs/chat/e-mail/fichiers) + **recherche unifiée cross-namespace** | 🔜 spec |
| 2 | **Métadonnées & schémas** | **A-17 `catalog`** — registre des schémas de données publiés par les apps (prolonge A-12 écosystème) | 🔜 spec |
| 3 | **Outils & API (function calling)** | **A-4b tool-calling + A-7 MCP + A-10 automation + A-11 execution** + **Action Registry** | 🔜 roadmap (confirmée/priorisée) |
| 3 | **Feedback** | **A-18 `feedback`** — corrections/validations → re-ranking RAG + few-shot mémoire + évals | 🔜 spec |

**Pièce centrale : le Context Assembler.** L'`AgentEngine` assemble déjà `mémoire + knowledge +
écosystème`. On le généralise en un **assembleur de contexte** qui agrège, pour une requête :
`profil` + `activité récente` + `état applicatif live` + `knowledge/RAG` + `écosystème` +
`schémas`, sous **budget de tokens** et **selon les droits**. A-13 y branche déjà l'activité.

---

## 2. Nouveaux modules (contrats)

### A-13 `activity` — Journal d'actions (LIVRÉ)
- **But :** savoir *ce que l'utilisateur a fait récemment* dans la suite.
- **Modèle d'événement** (neutre, publié par les apps via API) : `app`, `action`, `target?`,
  `status?` (ok/error), `detail?` (libre, **chiffré**), `ts` (ISO 8601), `session_id?`, `meta?`.
- **API :** `POST /v1/activity/log` (+ `log_batch`), `GET /v1/activity/timeline`,
  `POST /v1/activity/search` (sémantique), `GET /v1/activity/summary` (résumé LLM de la période),
  `DELETE /v1/activity/{user}` (droit à l'effacement / rétention).
- **Persistance :** StoragePort ns `activity:{user}` (clé triable par ts) + VectorPort pour la
  recherche sémantique. Champ `detail` chiffré (cipher mémoire).
- **Inspiration (concepts, pas de code) :** ActivityWatch/Tockler (timeline d'activité),
  Auditum (journal d'audit immuable), Kimai (agrégation par activité/temps).

### A-14 `profile` — Profil & préférences comportementales
- Cache : rôle(s), préférences UI, langue, habitudes **dérivées de l'activité** (apps les plus
  utilisées, heures actives). **Source de vérité identité/RBAC = Platform** (adaptateur read-only
  optionnel) ; hors Platform, profil local minimal.
- API : `GET/PUT /v1/profile/{user}`, `GET /v1/profile/{user}/habits` (calculées).

### A-15 `context` — Assembleur de contexte (temporel/spatial + agrégation)
- `POST /v1/context/assemble` → contexte unifié (profil + activité + appstate + knowledge +
  écosystème + schémas), borné en tokens, respectant les droits. Le module `agents` l'utilise.
- Contexte temporel/spatial : fuseau, moment de journée, locale, localisation **si fournie et
  consentie** (jamais de géoloc autonome).

### A-16 `appstate` — État applicatif en direct
- Canal **éphémère** (TTL court) : écran courant, brouillon de formulaire, dernière erreur.
- API : `PUT /v1/appstate/{user}` (upsert avec TTL), `GET /v1/appstate/{user}`.
- **Pas de session-replay** (on ne rejoue pas l'écran comme OpenReplay/rrweb) : on capte l'**état
  utile au raisonnement**, minimisé.

### A-17 `catalog` — Métadonnées & schémas de données
- Registre des **schémas** publiés par les apps (types de fichiers, tables/colonnes, formats),
  pour que l'IA comprenne les données manipulées. Prolonge le registre écosystème (A-12).
- API : `POST /v1/catalog/register`, `GET /v1/catalog/schemas`, `POST /v1/catalog/resolve`.

### A-18 `feedback` — Rétroaction & apprentissage
- Capture `up/down`, correction, validation, liés à une réponse/trace.
- Effets : **re-ranking** des sources RAG, **few-shot** injecté depuis la mémoire, jeu d'**évals**.
- API : `POST /v1/feedback`, `GET /v1/feedback/stats`.

### Action Registry (axe 3, transverse aux A-4b/A-7/A-10/A-11)
- Les apps **déclarent leurs actions exécutables** (`calendar.event.create`, `finance.row.update`,
  `mail.send`…) avec schéma d'entrée → l'AI Engine les expose comme **outils** aux agents (via
  tool-calling A-4b et/ou serveur MCP A-7), avec garde-fous (confirmation, droits, dry-run).

---

## 3. Le Context Assembler (détail)

```
requête agent
  ├─ profil (A-14)                     → rôle, langue, préférences
  ├─ activité récente (A-13)           → N dernières actions + résumé
  ├─ état applicatif live (A-16)       → écran/brouillon/erreur courante
  ├─ knowledge + RAG (A-3 / A-2)       → documents/e-mails/chat pertinents
  ├─ écosystème (A-12)                 → apps Lunziko concernées + fonctions
  └─ schémas (A-17)                    → structures de données en jeu
        ↓  (budget de tokens, filtrage par droits, PII minimisée)
   CONTEXTE UNIFIÉ  →  system prompt de l'agent  →  réponse / action
```

L'`AgentEngine` actuel en implémente déjà un sous-ensemble (mémoire + knowledge + écosystème).
A-13 ajoute l'**activité récente**. Les phases suivantes complètent l'assembleur.

---

## 4. Confidentialité & gouvernance

- **Chiffrement** des champs libres (detail/brouillons) via le cipher AES-256-GCM existant.
- **Rétention/TTL** : activité purgamble par âge ; appstate éphémère ; droit à l'effacement.
- **Consentement & minimisation** : localisation seulement si fournie ; pas de capture autonome.
- **Droits hérités** : le contexte assemblé ne dépasse jamais les droits de l'utilisateur (RBAC
  Platform quand branché).
- **Souveraineté** : tout reste local par défaut ; aucun envoi vers un tiers.

---

## 5. Roadmap proposée (ordre recommandé)

1. **A-13 `activity`** — socle comportemental (✅ livré).
2. **A-16 `appstate`** — état live (petit, à fort effet immédiat).
3. **A-14 `profile`** — profil/habitudes (consomme Platform en lecture seule).
4. **A-15 `context`** — assembleur unifié + contexte temporel/spatial.
5. **Extension RAG** — connecteurs + recherche unifiée cross-namespace.
6. **A-17 `catalog`** — schémas/métadonnées.
7. **A-18 `feedback`** — boucle d'amélioration.
8. **Action Registry + A-4b/A-7** — passage à l'exécution (function calling / MCP).

> Chaque phase : clean-room, offline-testable, ports existants, arrêt + validation avant la suivante.

---

## 6. A-13 — Activity & Events (LIVRÉ)

Première brique concrète. Module `ai_engine/modules/activity/` :
- `engine.py` : `ActivityEngine` (log/log_batch/timeline/search/summary/clear) sur StoragePort +
  VectorPort ; `detail` chiffré via le cipher mémoire ; résumé via le Provider Manager.
- `router.py` : `/v1/activity/{log,log-batch,timeline,search,summary}` + `DELETE /v1/activity/{user}`.
- **Intégration Context Assembler** : `AgentEngine.run` injecte les **actions récentes** de
  l'utilisateur (option `use_activity`, défaut true) dans le contexte système.
- Validé end-to-end **hors-ligne** (embedder hash, cipher dev) : log, timeline triée,
  recherche sémantique, résumé.

---

## 7. Annexe — Analyse de licences des sources citées (clean-room)

> **Règle absolue :** inspiration conceptuelle uniquement, **aucune copie**. Les sources
> **AGPL / BSL / fair-code / ELv2** sont **à ne pas étudier au niveau du code** (risque de
> contamination) — on part des concepts publics/documentation.

| Source | Licence (à confirmer au moment d'étudier) | Verdict |
|---|---|---|
| ActivityWatch | MPL-2.0 (copyleft de fichier) | inspiration concept uniquement |
| Auditum | permissive probable (à confirmer) | inspiration |
| Tockler | GPL-3.0 ⛔ | concept seulement, ne pas lire le code |
| Kimai | **AGPL-3.0 ⛔** | concept seulement |
| Keycloak / Authelia | Apache-2.0 | **non recodés** — Platform est l'autorité identité |
| PostHog | MIT (+ modules non-OSS) | inspiration analytics |
| cal.com | **AGPL-3.0 ⛔** | concept seulement |
| super-productivity | MIT | inspiration |
| Joplin | **AGPL-3.0 ⛔** | concept seulement |
| OpenReplay | ELv2 (restrictive) ⛔ | on ne fait PAS de session-replay |
| Sentry | **BSL/FSL (non-OSI) ⛔** | concept d'error-tracking seulement |
| GlitchTip | permissive probable (à confirmer) | inspiration |
| rrweb | MIT | inspiration (mais pas de replay) |
| Dify | Apache-2.0 + conditions | inspiration orchestration |
| RAGFlow | Apache-2.0 | inspiration RAG |
| Onyx (ex-Danswer) | MIT (+ EE) | inspiration recherche unifiée |
| OpenMetadata | Apache-2.0 | inspiration catalogue/schémas |
| n8n | **Sustainable Use (fair-code, non-OSI) ⛔** | clean-room déjà acté (A-10) |
| Flowise | Apache-2.0 (+ conditions) | inspiration |
| Langflow | MIT | inspiration |
| OpenHands | MIT | inspiration execution agent (A-11) |
| Langfuse | MIT (core, + EE) | inspiration observabilité/feedback |
| Label Studio | Apache-2.0 (community) | inspiration annotation/feedback |
| Fider | **AGPL-3.0 ⛔** | concept feedback seulement |

⚠️ Ces licences sont indicatives (cutoff des connaissances) et **doivent être revérifiées** avant
toute étude rapprochée d'un dépôt. La discipline clean-room rend le résultat propriété Lunziko.

---

## 8. Décisions à valider (avant de coder au-delà d'A-13)

- **D-CTX-01** — Frontière profil/RBAC : confirmer que l'AI Engine **consomme** l'identité de
  Platform (adaptateur read-only) et n'en héberge qu'un cache. *(reco : oui)*
- **D-CTX-02** — État applicatif : capter l'**état utile** (écran/brouillon/erreur) **sans
  session-replay**. *(reco : oui, minimisation)*
- **D-CTX-03** — Ordre d'implémentation : suivre §5 (activity → appstate → profile → assembler …).
- **D-CTX-04** — Chiffrement/rétention par défaut des données de contexte (TTL activité, TTL appstate).
- **D-CTX-05** — Action Registry : format de déclaration des actions exécutables par les apps.
