# IOE Entrance RAG

A retrieval-augmented Q&A app over your IOE entrance exam PDFs (Nepali +
English, including scanned pages that need OCR). Python/FastAPI backend,
React frontend.

## What this is, relative to the proposal PDF you shared

Your proposal describes an enterprise-scale, multi-agent Nepal-government
RAG system (six architecture layers, ministry-level NER, hybrid BM25 +
vector retrieval, a planner/synthesizer/critic agent loop, PostgreSQL +
a dedicated vector DB). That's the right shape for the *written*
proposal, and for a mid-term/final defense you can describe it as your
target architecture. What's actually feasible to build and demo for a
minor project by one student, working with 4 PDFs, is a scoped-down
slice of the same pipeline:

| Proposal layer | This app |
|---|---|
| Data Acquisition | Manual: you drop 4 PDFs in `backend/data/raw/` |
| Data Normalisation (OCR, Preeti→Unicode, language detection) | `pdf_extractor.py`: pdfplumber + pytesseract (eng+nep), Devanagari-range language detection. *(Preeti/Kantipur legacy-font conversion is not implemented — only needed if a PDF uses that old encoding rather than Unicode Devanagari; flag me if one of your 4 does.)* |
| Data Structuring & Chunking | `chunker.py`: page-aware sliding-window chunks |
| Knowledge Store | ChromaDB (local, embedded) instead of Postgres + a separate vector DB |
| Query Intelligence / Research Planning / Multi-agent execution | Not implemented — one retrieval pass, one LLM call |
| Domain Retrieval Engine | `vector_store.py`: cosine similarity search over multilingual-e5-large embeddings |
| Evidence Synthesis + Answer Generation | `rag_pipeline.py`: numbered, cited context → OpenAI chat completion |

This gives you a real, working, demoable app instead of an unbuilt
diagram, and it's honest about which parts are simplified — useful for
the "limitations / future work" section of a defense. See
`backend/README.md` → *Next steps* for how to add hybrid search,
reranking, or query rewriting if you want to close that gap further.

## Quickstart

```bash
# 1. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # add your OPENAI_API_KEY
mkdir -p data/raw         # copy your 4 PDFs here
python -m scripts.ingest
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the sidebar shows what's indexed, upload
box adds new PDFs live, and the chat pane answers with page citations.

## Project layout

```
backend/
  app/
    ingestion/     PDF → text (digital + OCR), one ingest_service used by both API and CLI
    processing/     text → chunks
    embeddings/     chunks/queries → vectors (multilingual-e5-large)
    retrieval/      ChromaDB vector store
    generation/      cited context → LLM answer
    api/            FastAPI routes + schemas
  scripts/ingest.py  batch-index everything in data/raw
frontend/
  src/App.jsx, components/  chat UI, upload, source citations
```
