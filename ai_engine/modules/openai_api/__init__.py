"""Compat OpenAI — expose /v1/chat/completions, /v1/embeddings, /v1/models au format OpenAI.

Fait de l'AI Engine un drop-in pour Open WebUI, LocalAI clients, Continue, Cline… en
réutilisant le ProviderManager (routage + fallback) et l'EmbeddingManager. Aucun couplage.
"""
