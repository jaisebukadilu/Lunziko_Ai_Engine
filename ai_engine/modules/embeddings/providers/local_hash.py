"""Embedder local « hash » — 100% hors-ligne, zéro dépendance, déterministe.

Repli ultime garantissant que le RAG fonctionne SANS réseau ni modèle : projection
par hachage de tri-grammes de caractères dans un vecteur de dimension fixe, puis
normalisation L2. Qualité modeste (lexicale) mais suffisante pour un fallback autonome.
"""

from __future__ import annotations

import hashlib
import math
import re


class HashEmbedder:
    name = "hash"

    def __init__(self, dim: int = 256) -> None:
        self._dim = max(16, dim)

    def available(self) -> bool:
        return True  # toujours disponible

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        tokens = re.findall(r"\w+", text.lower())
        # tri-grammes de caractères par token (capte la morphologie)
        for tok in tokens:
            padded = f"  {tok} "
            grams = [padded[i:i + 3] for i in range(len(padded) - 2)] or [tok]
            for g in grams:
                h = int.from_bytes(hashlib.md5(g.encode("utf-8")).digest()[:4], "big")
                idx = h % self._dim
                sign = 1.0 if (h >> 31) & 1 else -1.0
                vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]
