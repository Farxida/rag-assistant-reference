from sentence_transformers import CrossEncoder

_reranker = None
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker

def rerank(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    if not results:
        return []

    reranker = get_reranker()
    pairs = [(query, r["text"]) for r in results]
    scores = reranker.predict(pairs)

    for i, r in enumerate(results):
        r["rerank_score"] = float(scores[i])

    return sorted(results, key=lambda x: x["rerank_score"], reverse=True)[:top_k]

if __name__ == "__main__":
    from src.retrieval.hybrid import hybrid_search

    query = "What is the maximum file upload size?"
    candidates = hybrid_search(query, top_k=10)
    print("Before rerank:")
    for i, r in enumerate(candidates):
        print(f"  {i+1}. [{r['source']}] {r['text'][:80]}...")

    reranked = rerank(query, candidates, top_k=5)
    print("\nAfter rerank:")
    for i, r in enumerate(reranked):
        print(f"  {i+1}. (score={r['rerank_score']:.3f}) [{r['source']}] {r['text'][:80]}...")
