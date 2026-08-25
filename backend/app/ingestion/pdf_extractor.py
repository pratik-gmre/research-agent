"""
Extracts text from PDFs for the IOE entrance-exam knowledge base.

Two extraction paths per page:
  1. Digital text via pdfplumber (fast, exact) - used whenever a page
     already contains a real text layer.
  2. OCR via pytesseract (eng+nep) - used when a page has little/no
     digital text, which is the case for scanned/photocopied papers.

System requirements for OCR (see backend/README.md):
    sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-nep
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pdfplumber

from app.ingestion.preeti_converter import fix_preeti_encoding

logger = logging.getLogger(__name__)

MIN_DIGITAL_TEXT_CHARS = 20
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_LATIN_RE = re.compile(r"[A-Za-z]")

ExtractionMethod = Literal["digital", "ocr"]
LanguageHint = Literal["nepali", "english", "mixed", "unknown"]


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    method: ExtractionMethod
    language: LanguageHint
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


@dataclass
class ExtractedDocument:
    source_path: Path
    pages: list[ExtractedPage]

    @property
    def total_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

    @property
    def ocr_page_count(self) -> int:
        return sum(1 for p in self.pages if p.method == "ocr")


def detect_language(text: str) -> LanguageHint:
    has_dev = bool(_DEVANAGARI_RE.search(text))
    has_latin = bool(_LATIN_RE.search(text))
    if has_dev and has_latin:
        return "mixed"
    if has_dev:
        return "nepali"
    if has_latin:
        return "english"
    return "unknown"


class PDFExtractor:
    def __init__(
        self,
        ocr_languages: str = "eng+nep",
        min_digital_chars: int = MIN_DIGITAL_TEXT_CHARS,
        ocr_dpi: int = 300,
    ) -> None:
        self.ocr_languages = ocr_languages
        self.min_digital_chars = min_digital_chars
        self.ocr_dpi = ocr_dpi

    def extract(self, pdf_path: str | Path) -> ExtractedDocument:
        pdf_path = Path(pdf_path)
        pages: list[ExtractedPage] = []

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                digital_text = (page.extract_text() or "").strip()
                table_text = self._extract_tables_as_text(page)
                # Both digital_text and table_text come from pdfplumber's
                # text layer, which is where legacy Preeti-font encoding
                # shows up - fix that before combining.
                digital_text = fix_preeti_encoding(digital_text)
                table_text = fix_preeti_encoding(table_text)
                combined_text = "\n\n".join(t for t in [digital_text, table_text] if t)

                if len(digital_text) >= self.min_digital_chars:
                    pages.append(
                        ExtractedPage(
                            page_number=i,
                            text=combined_text,
                            method="digital",
                            language=detect_language(combined_text),
                        )
                    )
                else:
                    logger.info(
                        "%s page %d: little digital text (%d chars), using OCR",
                        pdf_path.name, i, len(digital_text),
                    )
                    ocr_text = self._ocr_page(pdf_path, i)
                    # table_text was already Preeti-corrected above; ocr_text
                    # is real Unicode from Tesseract and needs no fixing.
                    combined_ocr_text = "\n\n".join(t for t in [ocr_text, table_text] if t)
                    pages.append(
                        ExtractedPage(
                            page_number=i,
                            text=combined_ocr_text,
                            method="ocr",
                            language=detect_language(combined_ocr_text),
                        )
                    )

        return ExtractedDocument(source_path=pdf_path, pages=pages)

    def _extract_tables_as_text(self, page) -> str:
        """pdfplumber's extract_text() often drops or garbles table content
        (schedules, fee tables, marking schemes are usually tables). Pull
        tables separately and render them as simple pipe-separated rows so
        the data actually makes it into the index."""
        try:
            tables = page.extract_tables()
        except Exception:
            return ""

        rendered = []
        for table in tables:
            for row in table:
                cells = [str(c).strip() if c is not None else "" for c in row]
                if any(cells):
                    rendered.append(" | ".join(cells))
        return "\n".join(rendered)

    def _ocr_page(self, pdf_path: Path, page_number: int) -> str:
        import pytesseract
        from pdf2image import convert_from_path

        images = convert_from_path(
            str(pdf_path), dpi=self.ocr_dpi,
            first_page=page_number, last_page=page_number,
        )
        if not images:
            return ""
        return pytesseract.image_to_string(images[0], lang=self.ocr_languages).strip()


def extract_pdf(pdf_path: str | Path, **kwargs) -> ExtractedDocument:
    return PDFExtractor(**kwargs).extract(pdf_path)
