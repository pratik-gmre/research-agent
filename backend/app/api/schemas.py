from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


class SourceItem(BaseModel):
    index: int
    source_file: str
    page_number: int
    language: str
    method: str
    score: float
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]


class StatusResponse(BaseModel):
    indexed_chunks: int
    indexed_files: list[str]


class IngestResponse(BaseModel):
    filename: str
    pages: int
    ocr_pages: int
    chunks_added: int
