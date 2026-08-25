"""
The retrieve -> synthesize -> generate pipeline.

This is a deliberately simple, single-stage version of the multi-stage
RAG architecture from the project proposal (Query Intelligence ->
Research Planning -> Domain Retrieval -> Evidence Synthesis -> Answer
Generation). For a minor project's scope, those five stages collapse
into: retrieve top-k chunks -> build a numbered, cited context block
-> ask the LLM to answer using only that context. The stage boundaries
are kept as separate functions/files so any one of them (e.g. adding a
query-rewriting step, or a reranker) can be extended later without
restructuring the rest - see backend/README.md for suggested next steps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.generation.llm_client import generate_answer
from app.retrieval.vector_store import get_vector_store
from app.config import settings

# Questions that ask to enumerate/list things ("all colleges", "list the
# syllabus", "के के छन्", "सबै campus") need much higher recall than a
# normal factual question, because the relevant content is often spread
# across multiple, differently-worded sections of the source document
# (e.g. "constituent campuses" and "affiliated colleges" are two separate
# sections in the booklet, using different vocabulary). A fixed small
# top_k reliably misses one of them. Since this corpus is small (a
# few hundred chunks at most), it's cheap to just retrieve a lot more
# for these queries instead of building full hybrid/multi-hop retrieval.
_BROAD_QUERY_MARKERS = [
    "list", "all ", "every ", "each ", "what are the", "mention",
    "सूची", "सबै", "के के", "कुन कुन", "जम्मा",
]
BROAD_QUERY_TOP_K = 25

SYSTEM_PROMPT = """You are a study assistant for students preparing for the \
IOE (Institute of Engineering, Tribhuvan University) entrance exam.

Answer ONLY using the numbered SOURCE excerpts given to you. Rules:
- Every claim you make must be supported by at least one source. Cite \
sources inline like [1], [2] right after the sentence they support.
- If the sources don't contain enough information to answer, say so \
plainly instead of guessing or using outside knowledge.
- Match the language of the CURRENT question, not the language of the \
source excerpts. If the sources are in Nepali but the student asked in \
English, answer in English (and vice versa). Only switch languages if \
the student's question itself switches.
- When asked something broad like "list the syllabus" or "what topics \
are covered," check every numbered source for a distinct topic/chapter \
before answering, and list all of them - don't stop after the first few.
- Keep answers exam-focused: direct, structured, and precise. Show \
worked steps for numerical/physics/math questions.
"""


@dataclass
class RAGAnswer:
    answer: str
    sources: list[dict]


def _build_context_block(hits: list[dict]) -> str:
    lines = []
    for i, hit in enumerate(hits, start=1):
        meta = hit["metadata"]
        lines.append(
            f"[{i}] (source: {meta['source_file']}, page {meta['page_number']})\n"
            f"{hit['text']}"
        )
    return "\n\n".join(lines)


def _is_broad_query(question: str) -> bool:
    q = question.lower()
    return any(marker in q for marker in _BROAD_QUERY_MARKERS)


def answer_question(question: str, top_k: int | None = None) -> RAGAnswer:
    if top_k is None:
        top_k = BROAD_QUERY_TOP_K if _is_broad_query(question) else settings.top_k

    store = get_vector_store()
    hits = store.query(question, top_k=top_k)

    if not hits:
        return RAGAnswer(
            answer=(
                "I don't have any indexed material yet. Add your PDFs to "
                "data/raw and run the ingestion script first."
            ),
            sources=[],
        )

    context_block = _build_context_block(hits)
    user_prompt = (
        f"SOURCES:\n{context_block}\n\n"
        f"QUESTION: {question}\n\n"
        f"Answer the question using only the numbered sources above."
    )

    answer_text = generate_answer(SYSTEM_PROMPT, user_prompt)

    sources = [
        {
            "index": i + 1,
            "source_file": hit["metadata"]["source_file"],
            "page_number": hit["metadata"]["page_number"],
            "language": hit["metadata"]["language"],
            "method": hit["metadata"]["method"],
            "score": round(hit["score"], 3),
            "excerpt": hit["text"][:280],
        }
        for i, hit in enumerate(hits)
    ]

    return RAGAnswer(answer=answer_text, sources=sources)
