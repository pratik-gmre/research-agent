"""
Batch-ingest every PDF in data/raw into the vector store.

Usage:
    cd backend
    python -m scripts.ingest
"""

from pathlib import Path

from app.config import settings
from app.ingestion.ingest_service import ingest_pdf


def main() -> None:
    raw_dir = Path(settings.raw_data_dir)
    pdf_paths = sorted(raw_dir.glob("*.pdf"))

    if not pdf_paths:
        print(f"No PDFs found in {raw_dir.resolve()}. Add your exam PDFs there first.")
        return

    print(f"Found {len(pdf_paths)} PDF(s) in {raw_dir.resolve()}\n")

    for pdf_path in pdf_paths:
        print(f"Ingesting {pdf_path.name} ...")
        result = ingest_pdf(pdf_path)
        print(
            f"  pages={result['pages']} "
            f"ocr_pages={result['ocr_pages']} "
            f"chunks_added={result['chunks_added']}\n"
        )

    print("Done.")


if __name__ == "__main__":
    main()
