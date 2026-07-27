"""CRAG-lite — Corrective RAG (Yan et al., 2024, arXiv:2401.15884).

Retrieval sometimes returns weak context (odd phrasing, vocabulary mismatch).
Instead of blindly feeding it to the LLM, we GRADE the retrieved passages and,
if they are weak, REWRITE the query and search again.

Pipeline: hybrid(top20) -> rerank(top3) -> LLM grader (structured output)
    good -> return as is
    weak -> rewritten query -> second hybrid+rerank -> merge best

The grader is a small fast model; worst case +1 cheap call per query,
best case 0 extra calls (batch grading in a single call).
Fails open: if the grader errors out, plain retrieval results are returned.
"""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import rerank

load_dotenv()

GRADER_MODEL = "llama-3.1-8b-instant"

_grader = None  # lazy singleton


class ContextGrade(BaseModel):
    """Structured output of the grader: passage usefulness + backup query."""

    relevant: list[bool] = Field(
        description="For each passage in order: does it help answer the query?"
    )
    rewritten_query: str = Field(
        description="Better search query (synonyms, key terms). "
                    "Empty string if passages are sufficient."
    )


def _get_grader():
    global _grader
    if _grader is None:
        from langchain_groq import ChatGroq
        _grader = ChatGroq(
            model=GRADER_MODEL,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            max_retries=3,
        ).with_structured_output(ContextGrade)
    return _grader


GRADE_PROMPT = """You are a retrieval quality grader for a SaaS product knowledge base.

Query: {query}

Passages:
{passages}

For each passage decide if it helps answer the query. If most passages are \
irrelevant, propose a rewritten search query with better keywords."""


def _format_passages(results: list[dict]) -> str:
    return "\n".join(
        f"[{i + 1}] ({r.get('source', '?')}) {r['text'][:300]}"
        for i, r in enumerate(results)
    )


def corrective_search(query: str, top_k: int = 3) -> dict:
    """Retrieval with self-correction.

    Returns: {results, corrected: bool, rewritten_query: str | None}
    """
    candidates = hybrid_search(query, top_k=20)
    results = rerank(query, candidates, top_k=top_k)

    if not results:
        return {"results": [], "corrected": False, "rewritten_query": None}

    try:
        grade: ContextGrade = _get_grader().invoke(
            GRADE_PROMPT.format(query=query, passages=_format_passages(results))
        )
    except Exception:
        # grader down (rate limit etc.) -> degrade gracefully
        return {"results": results, "corrected": False, "rewritten_query": None}

    flags = list(grade.relevant)[: len(results)]
    n_good = sum(flags)

    if n_good >= 2 or not grade.rewritten_query.strip():
        return {"results": results, "corrected": False, "rewritten_query": None}

    new_query = grade.rewritten_query.strip()
    candidates2 = hybrid_search(new_query, top_k=20)
    results2 = rerank(new_query, candidates2, top_k=top_k)

    kept = [r for r, ok in zip(results, flags) if ok]
    seen = {r["text"][:80] for r in kept}
    for r in results2:
        if r["text"][:80] not in seen and len(kept) < top_k:
            kept.append(r)
            seen.add(r["text"][:80])

    return {"results": kept or results2[:top_k],
            "corrected": True,
            "rewritten_query": new_query}
