import time
from fastapi import FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.privacy.data_subject import (
    DISCLOSURE_TEXT,
    delete_user_data,
    export_user_data,
)
from src.retrieval.rag import RAGPipeline

limiter = Limiter(key_func=get_remote_address, default_limits=["100/day", "10/minute"])

app = FastAPI(
    title="RAG Assistant",
    description="Customer support RAG over a knowledge base of markdown documents.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator(
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, include_in_schema=False)

_rag: RAGPipeline | None = None

def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, examples=["How much is the Business plan?"])
    top_k: int = Field(5, ge=1, le=20)

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    latency_ms: float
    response_id: str
    cache_hit: bool

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/disclosure")
def disclosure():
    return {"message": DISCLOSURE_TEXT}


@app.get("/privacy/user/{user_id}/export")
def export_user(user_id: str):
    return export_user_data(user_id)


@app.delete("/privacy/user/{user_id}")
def delete_user(user_id: str):
    return delete_user_data(user_id)


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, req: ChatRequest):
    try:
        rag = get_rag()
        result = rag.query(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        latency_ms=result["latency_ms"],
        response_id=result["response_id"],
        cache_hit=result.get("cache_hit", False),
    )
