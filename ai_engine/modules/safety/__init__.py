"""Module safety — Safety Engine (garde-fous) de LAIA.

Filtrage entrée/sortie : **redaction PII** (e-mails, téléphones, cartes, IBAN), détection
d'**injection de prompt**, modération heuristique. Offline, sans modèle. Complète Validation
(structure) et Evaluation (qualité) par la dimension **sécurité**.
"""
