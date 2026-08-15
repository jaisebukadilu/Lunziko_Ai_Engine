# LAIA — Lunziko AI Intelligence Architecture

> **Lunziko AI Engine** évolue d'un « moteur d'IA » vers la **plateforme d'intelligence orchestrée**
> de l'écosystème Lunziko : plusieurs **cerveaux** spécialisés (Brains), plusieurs **moteurs**
> d'exécution/connaissance (Engines), des agents et des outils — pour comprendre une tâche,
> choisir les capacités, collaborer entre apps, exécuter, **valider** et accompagner jusqu'au but.
>
> **Principe : One AI Engine → Multiple Brains → Multiple Engines → Multiple Agents → Multiple
> Tools → One Unified Intelligence.**
>
> **Règle d'or : on NE remplace PAS l'architecture actuelle — on construit AU-DESSUS.** Les 23
> modules existants (provider, neural, rag, memory, knowledge, agent, tools, context, assistant,
> handoff, automation, actions, data, ecosystem, activity, feedback, catalog, code, voice, mcp…)
> deviennent des **Engines** de LAIA ; l'orchestrateur les coordonne sans les modifier.

## Les 3 niveaux

```
                LUNZIKO AI ENGINE (Intelligence Core)
                              │
                     AI ORCHESTRATOR (chef d'orchestre)
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   🧠 AI BRAINS          ⚙️ AI ENGINES          🛠️ AI TOOLS
  intelligence spéc.    infra/traitement       action
```

- **Brain** = *penser / comprendre / générer* (modèle ou config spécialisée).
- **Engine** = *exécuter / transformer / rechercher / orchestrer* (un module existant).
- **Tool** = *agir* (registre d'outils A-4b + actions d'app).

## Le flux de l'Orchestrator

```
Utilisateur → Intent → Task Analysis → Context Assembly → Planning
→ Brain Selection → Engine Selection → Tool Selection → Execution
→ Validation → Correction/Retry → Résultat final
```

Chaque étape **réutilise** un module existant :
`Intent`→neural router · `Context`→context assembler · `Brains`→Brain Registry ·
`Engines`→Engine Registry · `Tools`→tool registry + actions · `Execution`→agent/tools/provider ·
`Validation`→Validation Engine · état partagé→**AI Blackboard**.

## Phase AI-CORE (fondations — implémentée)

| Composant | Rôle | Endpoint |
|---|---|---|
| **Brain Registry** | catalogue des cerveaux (manifestes) + résolution | `/v1/brains*` |
| **Engine Registry** | catalogue des moteurs (mappe les modules existants) | `/v1/engines*` |
| **AI Blackboard** | espace de travail partagé (état de tâche) | `/v1/blackboard*` |
| **Task Intelligence** | décompose un objectif → sous-tâches + Brain assigné | `/v1/orchestrator/plan` |
| **AI Orchestrator** | intent→contexte→plan→(exécution)→validation | `/v1/orchestrator/*` |
| **Validation Engine** | vérifie les artefacts (code/ui/data/text…) | `/v1/validate` |

## Catalogue des Brains (statut)

**Actifs** (servis par provider/engines existants) : `text`, `reasoning`, `code`, `data`,
`research`, `document`, `ui_ux`, `language`.
**Déclarés / planned** (nécessitent des modèles dédiés) : `vision`, `image`, `video`, `audio`,
`music`, `voice`, `3d`, `cad`.

Chaque Brain a un **manifeste** : `id, name, type, capabilities[], inputs[], outputs[],
engines[], tools[], status`. Une app peut **déclarer ses besoins** (`requires.brains/engines/
services`) — croisé avec le registre écosystème.

## Registres (source de vérité)

```
REGISTRY
├── Application Registry  (REGISTRE_ECOSYSTEME_LUNZIKO.md — source de vérité écosystème)
├── Brain Registry        (LAIA, /v1/brains)
├── Engine Registry       (LAIA, /v1/engines — mappe les modules)
└── Tool Registry         (A-4b, /v1/tools + /v1/actions)
```

## Collaboration & validation

- **Brain-to-Brain** : un Brain peut solliciter un autre Brain (via l'orchestrateur + blackboard).
- **AI Blackboard** : `task, context, plan, artifacts, decisions, brain_outputs, tool_outputs,
  errors, validation` — tous les agents/brains travaillent sur le MÊME état de tâche.
- **Validation Engine** : `generate → validate → (ok? done : repair)` avec validateurs par type.

## Roadmap au-dessus d'AI-CORE
- **AI-BRAINS** : activer progressivement vision/image/video/audio/voice/3d/cad quand les
  modèles/engines correspondants existent (Graphics Engine, Voice V-1…).
- **AI-ENGINES** : Code Execution Engine (sandbox), Search Engine (web), Image/Video/Audio/3D/UI
  Generation Engines, Evaluation Engine.
- **Positionnement** : *Lunziko AI Engine = système d'intelligence orchestrée de l'écosystème* —
  les apps restent indépendantes, l'intelligence est commune via contrats API versionnés.
