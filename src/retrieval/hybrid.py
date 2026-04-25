from rank_bm25 import BM25Okapi

from src.auth.context import UserContext, anonymous_context
from src.ingestion.embedder import search as vector_search, get_collection

_bm25_index = None
_bm25_docs = None

def _build_bm25_index():
    global _bm25_index, _bm25_docs

    collection = get_collection()
    all_data = collection.get(include=["documents", "metadatas"])

    _bm25_docs = []
    tokenized = []
    for i, doc in enumerate(all_data["documents"]):
        meta = all_data["metadatas"][i]
        _bm25_docs.append({
            "text": doc,
            "source": meta["source"],
            "chunk_id": meta["chunk_id"],
            "tenant_id": meta.get("tenant_id", "northwind-public"),
            "classification": meta.get("classification", "public"),
        })
        tokenized.append(doc.lower().split())

    _bm25_index = BM25Okapi(tokenized)
    return _bm25_index

def bm25_search(query: str, top_k: int = 20, user_ctx: UserContext | None = None) -> list[dict]:
    global _bm25_index, _bm25_docs

    if _bm25_index is None:
        _build_bm25_index()

    ctx = user_ctx or anonymous_context()
    tokenized_query = query.lower().split()
    scores = _bm25_index.get_scores(tokenized_query)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in ranked:
        if score <= 0:
            break
        doc = _bm25_docs[idx]
        if not ctx.can_see(doc["tenant_id"], doc["classification"]):
            continue
        results.append({
            "text": doc["text"],
            "source": doc["source"],
            "bm25_score": float(score),
        })
        if len(results) >= top_k:
            break
    return results

def hybrid_search(
    query: str,
    top_k: int = 5,
    vector_weight: float = 0.5,
    user_ctx: UserContext | None = None,
) -> list[dict]:
    k = 60
    ctx = user_ctx or anonymous_context()

    vector_results = vector_search(query, top_k=20, user_ctx=ctx)
    bm25_results = bm25_search(query, top_k=20, user_ctx=ctx)

    rrf_scores = {}

    for rank, r in enumerate(vector_results):
        key = r["text"][:100]
        if key not in rrf_scores:
            rrf_scores[key] = {"text": r["text"], "source": r["source"], "score": 0}
        rrf_scores[key]["score"] += vector_weight / (k + rank + 1)

    bm25_weight = 1 - vector_weight
    for rank, r in enumerate(bm25_results):
        key = r["text"][:100]
        if key not in rrf_scores:
            rrf_scores[key] = {"text": r["text"], "source": r["source"], "score": 0}
        rrf_scores[key]["score"] += bm25_weight / (k + rank + 1)

    return sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)[:top_k]

if __name__ == "__main__":
    queries = [
        "How much does Business plan cost",
        "TLS version security",
        "Slack integration",
    ]
    for q in queries:
        print(f"Q: {q}")
        for r in hybrid_search(q, top_k=3):
            print(f"  [{r['source']}] (rrf={r['score']:.4f}) {r['text'][:80]}...")
        print()
