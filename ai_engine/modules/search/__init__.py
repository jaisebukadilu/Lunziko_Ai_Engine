"""Module search — Search Engine web du Research Brain.

Backend **DuckDuckGo sans clé** par défaut (recherche immédiate, gratuite) ; backend **Google
Custom Search** optionnel si `AE_GOOGLE_API_KEY` + `AE_GOOGLE_CSE_ID` sont fournis. Résultats
normalisés {title, url, snippet}. Alimente le Research Brain + un outil `web_search`.
"""
