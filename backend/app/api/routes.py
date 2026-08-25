from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.api.schemas import QueryRequest, QueryResponse, StatusResponse, IngestResponse
from app.generation.rag_pipeline import answer_question
from app.ingestion.ingest_service import ingest_pdf
from app.retrieval.vector_store import get_vector_store
from app.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/status", response_model=StatusResponse)
def status():
    store = get_vector_store()
    return StatusResponse(
        indexed_chunks=store.document_count(),
        indexed_files=store.indexed_sources(),
    )


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")
    result = answer_question(request.question, top_k=request.top_k)
    return QueryResponse(answer=result.answer, sources=result.sources)


@router.post("/upload", response_model=IngestResponse)
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only .pdf files are supported")

    raw_dir = Path(settings.raw_data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest_path = raw_dir / file.filename

    with open(dest_path, "wb") as f:
        f.write(await file.read())

    result = ingest_pdf(dest_path)
    return IngestResponse(**result)
