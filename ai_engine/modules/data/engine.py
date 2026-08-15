"""DataEngine — orchestre nettoyage/préparation et fait le pont vers RAG et entraînement.

Prépare la « matière première » pour les autres piliers : indexation RAG des documents
nettoyés, corpus texte prêt pour le LLM natif, table d'exemples prête pour l'entraîneur ML.
"""

from __future__ import annotations

from ai_engine.modules.data.cleaner import clean_records, clean_texts, profile_records


class DataEngine:
    def profile(self, records: list[dict]) -> dict:
        return profile_records(records)

    def clean(self, records: list[dict], **opts) -> dict:
        return clean_records(records, **opts)

    def clean_texts(self, texts: list[str], **opts) -> dict:
        return clean_texts(texts, **opts)

    async def prepare_for_rag(
        self, namespace: str, texts: list[str], *, min_len: int = 1
    ) -> dict:
        """Nettoie puis indexe les documents dans le RAG (VectorPort)."""
        from ai_engine.modules.rag.service import get_rag_service

        cleaned = clean_texts(texts, min_len=min_len)
        rag = get_rag_service()
        indexed = 0
        for i, doc in enumerate(cleaned["texts"]):
            indexed += await rag.index(namespace, f"data-{i}", doc, {"source": "data.prepare"})
        return {"namespace": namespace, "documents": len(cleaned["texts"]),
                "chunks_indexed": indexed, "report": cleaned["report"]}

    def prepare_corpus(self, texts: list[str], *, min_len: int = 8) -> dict:
        """Assemble un corpus texte propre (pour entraîner le LLM natif lunziko-llm)."""
        cleaned = clean_texts(texts, min_len=min_len)
        corpus = "\n".join(cleaned["texts"])
        return {"corpus": corpus, "chars": len(corpus),
                "documents": len(cleaned["texts"]), "report": cleaned["report"]}

    def prepare_training(self, records: list[dict], *, text_field: str, label_field: str) -> dict:
        """Extrait des paires (texte, label) nettoyées pour l'entraîneur ML."""
        cleaned = clean_records(records)["records"]
        examples = [
            {"text": str(r[text_field]), "label": str(r[label_field])}
            for r in cleaned
            if r.get(text_field) not in (None, "") and r.get(label_field) not in (None, "")
        ]
        labels = sorted({e["label"] for e in examples})
        return {"examples": examples, "count": len(examples), "labels": labels}


def get_data_engine() -> DataEngine:
    return DataEngine()
