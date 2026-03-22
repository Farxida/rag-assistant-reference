"""FastAPI service exposing the RAG pipeline as REST."""

import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.retrieval.rag import RAGPipeline

app = FastAPI(
    title="RAG Assistant",
    description="Customer support RAG over a knowledge base of markdown documents.",
    version="0.1.0",
)

_rag: RAGPipeline | None = None


def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["How much is the Business plan?"])
    top_k: int = Field(5, ge=1, le=20)


class Source(BaseModel):
    source: str
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    latency_ms: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    t0 = time.time()
    try:
        rag = get_rag()
        result = rag.query(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=(time.time() - t0) * 1000,
    )
