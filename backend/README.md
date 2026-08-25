# IOE Entrance RAG — Backend

FastAPI service that answers questions over your IOE entrance exam PDFs
(English + Nepali, including scanned/OCR pages) using retrieval-augmented
generation.

## How a question is answered

```
PDF files (data/raw)
    │  PDFExtractor  (pdfplumber, falls back to pytesseract eng+nep OCR)
    ▼
ExtractedDocument (text per page, tagged digital/ocr, tagged language)
    │  chunk_document  (per-page sliding window, ~1200 chars, 200 overlap)
    ▼
Chunks (text + doc_id, source_file, page_number, language, method)
    │  embed_passages  (intfloat/multilingual-e5-large, local, free)
    ▼
ChromaDB vector index (data/chroma/, persisted on disk)

User question
    │  embed_query
    ▼
top-k similar chunks  ──►  numbered, cited context block
    │  generate_answer (OpenAI chat model)
    ▼
Answer with inline [1][2] citations + source list (file, page, score)
```

This mirrors the Data Pipeline → Knowledge Store → RAG layers from the
original project proposal, scoped down for a single-student minor
project: one retrieval pass instead of hybrid BM25+vector search, one
LLM call instead of a multi-agent planner/critic loop. See "Next steps"
below for how to grow it back toward the full architecture if you want
more depth for the defense.

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# OCR system dependencies (only needed if any of your PDFs are scanned)
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-nep
tesseract --list-langs          # confirm 'eng' and 'nep' are listed

cp .env.example .env
# edit .env and set OPENAI_API_KEY
```

## Add your PDFs and build the index

```bash
mkdir -p data/raw
# copy your 4 IOE entrance PDFs into backend/data/raw/

python -m scripts.ingest
```

The first run downloads the embedding model (~1GB) and can take a few
minutes; OCR pages are also slower than digital ones. Re-running is
safe — chunk IDs are stable, so re-ingesting the same PDF overwrites
its old chunks instead of duplicating them.

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

- `GET  /api/health`  — liveness check
- `GET  /api/status`  — how many chunks / which files are indexed
- `POST /api/upload`  — upload a new PDF (multipart `file`), ingests it immediately
- `POST /api/query`   — `{"question": "..."}` → `{"answer": "...", "sources": [...]}`

Interactive docs: http://localhost:8000/docs

## Next steps (if you want to extend this for your defense)

- **Hybrid retrieval**: add a BM25 keyword index (`rank_bm25`) alongside
  the vector search in `retrieval/vector_store.py` and merge the two
  rankings — helps with exact terms (formula names, proper nouns) that
  embeddings sometimes miss.
- **Reranker**: after the top-k vector hits, rerank with a cross-encoder
  (e.g. `BAAI/bge-reranker-v2-m3`) before building the context block.
- **Query rewriting**: expand short/ambiguous questions before
  embedding (a small extra LLM call in `rag_pipeline.py`).
- **Evaluation**: track Precision@K / MRR (retrieval) and a faithfulness
  check (generation) as described in the proposal, Section 5.8.
