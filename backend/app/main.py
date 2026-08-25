from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

app = FastAPI(
    title="IOE Entrance RAG API",
    description="Retrieval-augmented Q&A over IOE entrance exam PDFs (Nepali + English).",
    version="0.1.0",
)

# Loosened for local dev where the React app runs on a different port.
# Tighten this to your deployed frontend origin before shipping.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
