"""
BM25 keyword index, used alongside vector search.

Dense embeddings are good at "what does this mean" but weak at "does
this contain the literal token '2082' / 'cutoff' / 'Pulchowk'" -
exactly the kind of lookup that dominates this corpus (dates, ranks,
program names, campus names, numbers in tables). BM25 catches those
directly by exact/near-exact term overlap, which is why questions like
"cutoff rank 2082" or "exam duration" kept failing on vector search
alone even though the text was correctly indexed.

Tokenization is a simple \\w+ regex, which works for both English and
Devanagari since Python's re treats Unicode letters (including
Devanagari) as word characters by default.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class KeywordIndex:
    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunk_ids: list[str] = []

    def build(self, chunk_ids: list[str], texts: list[str]) -> None:
        self._chunk_ids = chunk_ids
        tokenized = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def query(self, question: str, top_k: int) -> list[tuple[str, float]]:
        """Returns (chunk_id, bm25_score) pairs, best first."""
        if self._bm25 is None or not self._chunk_ids:
            return []
        scores = self._bm25.get_scores(tokenize(question))
        ranked = sorted(zip(self._chunk_ids, scores), key=lambda pair: pair[1], reverse=True)
        return [(cid, score) for cid, score in ranked[:top_k] if score > 0]
