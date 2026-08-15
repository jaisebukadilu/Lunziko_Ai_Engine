"""RagService — relie embeddings, VectorPort et le Provider Manager.

- index  : découpe un document, l'embed et l'upsert dans le VectorPort.
- search : embed la requête et récupère les fragments les plus proches (cosinus).
- query  : search + réponse augmentée via le Provider Manager (RAG complet).
"""

from __future__ import annotations

from ai_engine.core.registry import get_vector
from ai_engine.modules.embeddings.manager import get_embedding_manager
from ai_engine.modules.provider.base import ChatMessage, ChatResult
from ai_engine.modules.provider.manager import get_provider_manager
from ai_engine.modules.rag.chunk import chunk_text

_RAG_SYSTEM = (
    "Tu réponds à partir du CONTEXTE fourni. Si l'information n'y est pas, dis-le "
    "clairement. Cite les passages pertinents. Réponds dans la langue de la question."
)


class RagService:
    def __init__(self) -> None:
        self._vec = get_vector()
        self._emb = get_embedding_manager()

    async def index(self, namespace: str, doc_id: str, text: str, meta: dict | None = None) -> int:
        chunks = chunk_text(text)
        if not chunks:
            return 0
        vectors = (await self._emb.embed(chunks)).vectors
        base_meta = meta or {}
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            self._vec.upsert(
                namespace,
                f"{doc_id}#{i}",
                vector,
                {"text": chunk, "doc_id": doc_id, "chunk": i, **base_meta},
            )
        return len(chunks)

    async def search(self, namespace: str, query: str, k: int = 5) -> list[dict]:
        qvec = (await self._emb.embed([query])).vectors[0]
        hits = self._vec.search(namespace, qvec, k)
        return [
            {
                "id": h["id"],
                "score": round(h["score"], 4),
                "text": (h.get("meta") or {}).get("text", ""),
                "meta": {k2: v for k2, v in (h.get("meta") or {}).items() if k2 != "text"},
            }
            for h in hits
        ]

    async def query(
        self,
        namespace: str,
        query: str,
        k: int = 5,
        provider: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> dict:
        hits = await self.search(namespace, query, k)
        context = "\n\n---\n\n".join(f"[{h['id']}] {h['text']}" for h in hits)
        sys = (system or _RAG_SYSTEM) + f"\n\nCONTEXTE:\n{context}"
        answer: ChatResult = await get_provider_manager().chat(
            [ChatMessage(role="user", content=query)],
            provider=provider,
            system=sys,
            max_tokens=max_tokens,
        )
        return {"answer": answer, "sources": hits}


def get_rag_service() -> RagService:
    # Instance légère à la demande (les ports sous-jacents sont, eux, mis en cache).
    return RagService()
