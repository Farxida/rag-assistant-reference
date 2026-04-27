import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.retrieval.rag import RAGPipeline

limiter = Limiter(key_func=get_remote_address, default_limits=["100/day", "10/minute"])

app = FastAPI(
    title="RAG Assistant",
    description="Customer support RAG over a knowledge base of markdown documents.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
