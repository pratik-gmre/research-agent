"""One place that turns 'a PDF on disk' into 'chunks in the vector store'."""

from __future__ import annotations

from pathlib import Path

from app.ingestion.pdf_extractor import PDFExtractor
from app.processing.chunker import chunk_document
from app.retrieval.vector_store import get_vector_store
from app.config import settings


def ingest_pdf(pdf_path: str | Path) -> dict:
    pdf_path = Path(pdf_path)
    extractor = PDFExtractor(ocr_languages=settings.ocr_languages)
    doc = extractor.extract(pdf_path)

    chunks = chunk_document(
        doc,
        chunk_size_chars=settings.chunk_size_chars,
        chunk_overlap_chars=settings.chunk_overlap_chars,
    )

    store = get_vector_store()
    store.add_chunks(chunks)

    return {
        "filename": pdf_path.name,
        "pages": doc.total_pages,
        "ocr_pages": doc.ocr_page_count,
        "chunks_added": len(chunks),
    }
