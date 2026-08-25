"""
Splits an ExtractedDocument into retrieval-sized chunks.

Chunking is done per page rather than across the whole document. This
keeps every chunk's citation exact ("page 7 of question-bank-2081.pdf")
which matters for an exam-prep tool where a student wants to jump back
to the source question, and avoids merging unrelated questions from
different pages into one chunk.

A page's text is split into windows of `chunk_size_chars` characters
with `chunk_overlap_chars` of overlap so a question that straddles a
window boundary isn't cut in a way that loses its answer/options.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.pdf_extractor import ExtractedDocument


@dataclass
class Chunk:
    chunk_id: str          # "{doc_id}::p{page}::c{index}"
    doc_id: str             # stable id for the source document (filename stem)
    source_file: str        # original filename, for display/citation
    page_number: int
    language: str
    method: str              # "digital" or "ocr" - lets the UI flag OCR'd (less certain) text
    text: str


def _window(text: str, size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    windows = []
    start = 0
    step = max(size - overlap, 1)
    while start < len(text):
        windows.append(text[start:start + size])
        start += step
    return windows


def chunk_document(
    doc: ExtractedDocument,
    chunk_size_chars: int = 1200,
    chunk_overlap_chars: int = 200,
) -> list[Chunk]:
    doc_id = doc.source_path.stem
    chunks: list[Chunk] = []

    for page in doc.pages:
        windows = _window(page.text, chunk_size_chars, chunk_overlap_chars)
        for i, window_text in enumerate(windows):
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}::p{page.page_number}::c{i}",
                    doc_id=doc_id,
                    source_file=doc.source_path.name,
                    page_number=page.page_number,
                    language=page.language,
                    method=page.method,
                    text=window_text,
                )
            )

    return chunks
