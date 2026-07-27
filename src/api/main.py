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
from src.cache.semantic_cache import SemanticCache

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
_agent = None  # LangGraph agent singleton (with per-thread dialogue memory)
_semantic_cache = SemanticCache()


def get_agent():
    global _agent
    if _agent is None:
        from src.agent.graph import create_agent
        _agent = create_agent(with_memory=True)
    return _agent

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


# ---------- Agentic endpoint (LangGraph graph with guardrails) ----------

import uuid


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, description="Dialogue memory thread")
    use_cache: bool = Field(default=True, description="Semantic cache for typical questions")


class AgentChatResponse(BaseModel):
    answer: str
    session_id: str
    intent: str | None
    tools_used: list[str]
    escalated: bool
    cached: bool = False
    latency_ms: int


@app.post("/agent/chat", response_model=AgentChatResponse)
@limiter.limit("10/minute")
def agent_chat(request: Request, req: AgentChatRequest):
    from src.agent.graph import run_agent

    session_id = req.session_id or str(uuid.uuid4())
    t0 = time.time()

    if req.use_cache:
        cached = _semantic_cache.lookup(req.message)
        if cached is not None:
            return AgentChatResponse(
                answer=cached["answer"], session_id=session_id,
                intent=cached["intent"], tools_used=cached["tools_used"],
                escalated=False, cached=True,
                latency_ms=int((time.time() - t0) * 1000),
            )

    try:
        result = run_agent(get_agent(), req.message, thread_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent failure: {type(e).__name__}")
    latency_ms = int((time.time() - t0) * 1000)

    if req.use_cache:
        _semantic_cache.store(req.message, result)

    return AgentChatResponse(
        answer=result["answer"], session_id=session_id, intent=result["intent"],
        tools_used=result["tools_used"], escalated=result["escalated"],
        cached=False, latency_ms=latency_ms,
    )


@app.get("/agent/cache/stats")
def agent_cache_stats():
    return _semantic_cache.stats()
