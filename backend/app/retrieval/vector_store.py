"""
Thin wrapper around a persistent local ChromaDB collection, combined
with a BM25 keyword index (see keyword_index.py) for hybrid retrieval.

ChromaDB is used instead of Qdrant/pgvector because it needs no
separate server process - the whole vector index lives in a folder on
disk, which keeps setup to `pip install` for a minor project demo.

Why hybrid: pure vector search under-retrieves exact terms (dates,
ranks, names, numbers) that dominate this corpus. Pure keyword search
would miss paraphrased/conceptual questions. Combining both with
Reciprocal Rank Fusion (RRF) - a simple, parameter-light way to merge
two ranked lists - gets the benefit of each without needing to tune a
blend weight.
"""

from __future__ import annotations

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.embeddings.embedder import embed_passages, embed_query
from app.processing.chunker import Chunk
from app.retrieval.keyword_index import KeywordIndex

COLLECTION_NAME = "ioe_entrance_knowledge_base"
RRF_K = 60  # standard RRF damping constant
FUSION_POOL_MULTIPLIER = 4  # pull this many x top_k from each method before fusing


class VectorStore:
    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._keyword_index = KeywordIndex()
        self._rebuild_keyword_index()

    def _rebuild_keyword_index(self) -> None:
        data = self._collection.get(include=["documents"])
        self._keyword_index.build(data["ids"], data["documents"])

    def add_chunks(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        embeddings = embed_passages([c.text for c in chunks])
        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "doc_id": c.doc_id,
                    "source_file": c.source_file,
                    "page_number": c.page_number,
                    "language": c.language,
                    "method": c.method,
                }
                for c in chunks
            ],
        )
        # Cheap to rebuild in full at this corpus size (hundreds of
        # chunks); avoids the complexity of incremental BM25 updates.
        self._rebuild_keyword_index()

    def query(self, question: str, top_k: int = 5) -> list[dict]:
        pool_size = top_k * FUSION_POOL_MULTIPLIER

        query_vector = embed_query(question)
        vector_result = self._collection.query(
            query_embeddings=[query_vector],
            n_results=min(pool_size, self._collection.count()),
        )
        vector_ranked_ids = vector_result["ids"][0] if vector_result["ids"] else []

        keyword_hits = self._keyword_index.query(question, pool_size)
        keyword_ranked_ids = [chunk_id for chunk_id, _ in keyword_hits]

        fused_ids = self._reciprocal_rank_fusion([vector_ranked_ids, keyword_ranked_ids])
        top_ids = fused_ids[:top_k]
        if not top_ids:
            return []

        fetched = self._collection.get(ids=top_ids, include=["documents", "metadatas"])
        by_id = {
            cid: {"text": doc, "metadata": meta}
            for cid, doc, meta in zip(fetched["ids"], fetched["documents"], fetched["metadatas"])
        }

        hits = []
        for rank, chunk_id in enumerate(top_ids):
            if chunk_id not in by_id:
                continue
            hits.append({
                "chunk_id": chunk_id,
                "text": by_id[chunk_id]["text"],
                "metadata": by_id[chunk_id]["metadata"],
                "score": round(1.0 - (rank / max(len(top_ids), 1)), 3),  # display-only relevance
            })
        return hits

    @staticmethod
    def _reciprocal_rank_fusion(ranked_lists: list[list[str]]) -> list[str]:
        scores: dict[str, float] = {}
        for ranked_list in ranked_lists:
            for rank, chunk_id in enumerate(ranked_list):
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)
        return [cid for cid, _ in sorted(scores.items(), key=lambda pair: pair[1], reverse=True)]

    def document_count(self) -> int:
        return self._collection.count()

    def indexed_sources(self) -> list[str]:
        data = self._collection.get(include=["metadatas"])
        return sorted({m["source_file"] for m in data["metadatas"]})

    def delete_by_source(self, source_file: str) -> int:
        """Remove every chunk that came from a given PDF filename."""
        matches = self._collection.get(
            where={"source_file": source_file}, include=[]
        )
        ids = matches["ids"]
        if ids:
            self._collection.delete(ids=ids)
            self._rebuild_keyword_index()
        return len(ids)


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
