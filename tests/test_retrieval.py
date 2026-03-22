"""Smoke tests for retrieval — assumes ChromaDB has been built (data/chroma_db)."""

import pytest

from src.ingestion.embedder import search, get_collection
from src.retrieval.hybrid import hybrid_search, bm25_search


@pytest.fixture(scope="module", autouse=True)
def require_chroma():
    try:
        get_collection()
    except Exception:
        pytest.skip("ChromaDB not built — run `python -m src.ingestion.build_knowledge_base` first")


def test_vector_search_returns_results():
    results = search("How much does the Business plan cost?", top_k=5)
    assert len(results) == 5
    assert all("text" in r and "source" in r for r in results)


def test_vector_search_finds_pricing():
    results = search("Business plan price per month", top_k=5)
    sources = [r["source"] for r in results]
    assert "pricing.md" in sources


def test_bm25_search_returns_results():
    results = bm25_search("Business plan", top_k=5)
    assert len(results) > 0
    assert all("bm25_score" in r for r in results)


def test_hybrid_search_combines_signals():
    results = hybrid_search("API authentication Bearer token", top_k=3)
    assert len(results) == 3
    assert all("score" in r for r in results)


def test_hybrid_search_finds_correct_doc_for_known_query():
    results = hybrid_search("How long are audit logs retained?", top_k=5)
    sources = [r["source"] for r in results]
    assert "policies.md" in sources
