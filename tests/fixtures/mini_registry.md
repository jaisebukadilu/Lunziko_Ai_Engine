# Registre de test (fixture) — écosystème Lunziko réduit

## 1. Roster complet des applications

### 1.A — Socle & services transverses (agrégateurs)

#### Lunziko AI Engine
- **Catégorie :** IA autonome de l'écosystème.
- **Statut :** fixture de test.
- **Fonctions exhaustives :**
  - **Chat :** génération de texte.
  - **RAG :** recherche augmentée.
- **Expose :** raisonnement, agents. **Consomme :** le registre.

### 1.B — Applications & suites métier

#### Lunziko One
- **Catégorie :** suite ERP métier modulaire.
- **Statut :** fixture de test.
- **Fonctions exhaustives :**
  - **Finance :** factures, trésorerie, comptes, écritures, rapprochement bancaire.
  - **RH :** effectifs, contrats, congés, paie.
  - **Ventes :** devis, commandes, clients.
- **Expose :** données métier. **Consomme :** BI, Platform.

#### Lunziko BI
- **Catégorie :** Business Intelligence et analytique.
- **Statut :** fixture de test.
- **Fonctions exhaustives :**
  - **Dashboards :** tableaux de bord, KPI, rapports.
  - **Données :** datasets, mesures, connecteurs.
- **Expose :** analytics, dashboards. **Consomme :** One, Platform.

#### DociaPub
- **Catégorie :** suite documentaire et bureautique.
- **Statut :** fixture de test.
- **Fonctions exhaustives :**
  - **MyWord :** traitement de texte.
  - **MySheet :** tableur.
- **Expose :** documents. **Consomme :** BI, Platform.

#### Lunziko CAD
- **Catégorie :** CAO / DAO.
- **Statut :** fixture de test.
- **Fonctions exhaustives :** modélisation 2D/3D paramétrique, extrude, revolve.
- **Expose :** modèles CAO. **Consomme :** Graphics Engine.

#### Lunziko VidiaPub
- **Catégorie :** suite créative.
- **Statut :** fixture de test.
- **Fonctions exhaustives :**
  - **Photo :** retouche d'image.
  - **Vidéo :** montage.
- **Expose :** création graphique. **Consomme :** Platform.
