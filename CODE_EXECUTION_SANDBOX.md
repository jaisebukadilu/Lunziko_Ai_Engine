# Code Execution Engine — cadrage sécurité (A-11)

> Le **Code Brain** doit pouvoir boucler `generate → run → observe error → fix → retest`.
> Exécuter du code est **intrinsèquement dangereux** : ce document fixe le modèle de sécurité.
> Principe : **sûr par défaut**, exécution réelle **opt-in explicite**, jamais dans le processus
> de l'AI Engine. Inspiration conceptuelle Open Interpreter (AGPL) — **clean-room, aucun code copié**.

## Modèle à deux niveaux

### Niveau 0 — Safe Evaluator (activé par défaut, réellement sûr)
- Évalue un **sous-ensemble d'expressions** Python via un **interpréteur AST restreint** :
  arithmétique, littéraux, listes/dicts/tuples, opérateurs booléens/comparaisons, quelques
  fonctions **pures** en liste blanche (`len, min, max, sum, abs, round, sorted, range`…).
- **Interdits** : `import`, appels de fonctions hors liste blanche, accès attributs (`__…__`),
  affectations arbitraires, boucles non bornées, I/O, réseau, système de fichiers.
- Aucun sous-processus, aucun effet de bord → utilisable partout, y compris hors-ligne.

### Niveau 1 — Sandbox subprocess (DÉSACTIVÉ par défaut, opt-in)
- Exécute du **vrai code** (python) dans un **sous-processus isolé** du moteur :
  - `python -I -S` (mode isolé, pas de site) ;
  - **répertoire de travail temporaire** jetable (nettoyé après) ;
  - **timeout** wall-clock (`AE_CODE_EXEC_TIMEOUT`, défaut 10 s) ;
  - **environnement minimal** (variables stripées) ;
  - **capture** stdout/stderr **plafonnée** (`AE_CODE_EXEC_MAX_OUTPUT`) ;
  - retour structuré `{stdout, stderr, exit_code, timed_out, duration}`.
- **Activation obligatoire** : `AE_CODE_EXEC_ENABLED=true`. Désactivé → l'endpoint refuse
  proprement (jamais d'exécution implicite).

## Ce que le sandbox intégré NE garantit PAS (et la recommandation)
Le sous-processus est une isolation **« soft »** (processus séparé + timeout + pas d'état
partagé). Il **ne coupe pas** de façon garantie le **réseau** ni l'accès **fichiers** hors du
temp dir (limites de portabilité Windows/macOS/Linux).

➡️ **Pour du code non fiable, exiger une isolation OS** en amont : conteneur (Docker/Podman),
`firejail`/`nsjail`/`bubblewrap` (Linux), microVM (Firecracker), ou l'exécuter sur une machine
jetable. Le Code Brain n'active le Niveau 1 que dans un tel environnement contrôlé.

## Décisions de cadrage (à valider)
- **D-EXEC-01** — Défaut = **désactivé** ; activation explicite par variable d'env. *(reco : oui)*
- **D-EXEC-02** — Langages autorisés au Niveau 1 : **python** d'abord (node/… ensuite si présents).
- **D-EXEC-03** — Timeout défaut **10 s**, sortie plafonnée **20 000 caractères**.
- **D-EXEC-04** — Isolation réseau/fichiers **déléguée à l'OS** (conteneur/firejail) pour code
  non fiable ; le sandbox intégré reste « soft ». *(reco : oui)*
- **D-EXEC-05** — Boucle `run→fix` du Code Brain : orchestrée côté LAIA (Reasoning/Code Brain),
  le moteur ne fait qu'exécuter et rapporter.

## Endpoints
- `GET  /v1/code-exec/status` — niveau disponible, activé ?, limites.
- `POST /v1/code-exec/eval`  — Niveau 0 (safe evaluator), toujours disponible.
- `POST /v1/code-exec/run`   — Niveau 1 (sandbox), **refuse** si `AE_CODE_EXEC_ENABLED=false`.
