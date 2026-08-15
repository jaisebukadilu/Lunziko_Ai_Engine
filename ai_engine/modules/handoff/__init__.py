"""Module handoff — redirection inter-applications & transfert/ouverture de fichiers.

Depuis une application, l'assistant peut, selon la situation : rediriger l'utilisateur vers
une autre app Lunziko pour poursuivre sa tâche, transférer un fichier/dossier vers une autre
app, ou proposer de l'ouvrir dans l'app la plus adaptée. Le moteur produit des **actions
structurées** (instructions) ; l'exécution réelle revient à l'app hôte / au HUB / à Platform.
"""
