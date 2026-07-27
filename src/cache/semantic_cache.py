"""Semantic cache — caches answers by question MEANING, not exact text.

Support questions repeat: "how much is the Business plan?", "Business plan
price?", "what does Business cost?" are the same question. An exact-match
cache (see response_cache.py) misses these; a semantic one catches them.

Mechanics: question -> embedding (same MiniLM already used for retrieval) ->
cosine similarity against cached entries -> above threshold -> return the
stored answer in ~10-30 ms instead of a full agent run.

Safety rules:
- only clean answers are cached: no escalations, no guardrail violations
- threshold is DATA-CALIBRATED: paraphrases of one question score 0.91-0.94,
  different questions (e.g. two different plan names) score <= 0.77 -> 0.88
  keeps a safe margin both ways
- TTL + FIFO eviction; callers can bypass with use_cache=False
"""

import time
from typing import Callable

import numpy as np


class SemanticCache:
    def __init__(self, threshold: float = 0.88, ttl_seconds: int = 24 * 3600,
                 max_entries: int = 500,
                 embed_fn: Callable[[str], np.ndarray] | None = None):
        self.threshold = threshold
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._embed_fn = embed_fn  # injectable for tests
        self._model = None
        self._embeddings: list[np.ndarray] = []
        self._entries: list[dict] = []
        self.hits = 0
        self.misses = 0

    def _embed(self, text: str) -> np.ndarray:
        if self._embed_fn is not None:
            v = np.asarray(self._embed_fn(text), dtype=np.float32)
            n = np.linalg.norm(v)
            return v / n if n else v
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model.encode([text], normalize_embeddings=True)[0].astype(np.float32)

    def _evict_expired(self):
        now = time.time()
        alive = [(e, v) for e, v in zip(self._entries, self._embeddings)
                 if now - e["ts"] < self.ttl]
        self._entries = [e for e, _ in alive]
        self._embeddings = [v for _, v in alive]

    def lookup(self, question: str) -> dict | None:
        self._evict_expired()
        if not self._entries:
            self.misses += 1
            return None
        q = self._embed(question)
        sims = np.stack(self._embeddings) @ q
        best = int(np.argmax(sims))
        if sims[best] >= self.threshold:
            self.hits += 1
            return self._entries[best]["response"]
        self.misses += 1
        return None

    def store(self, question: str, response: dict):
        """Cache ONLY answers that are safe to replay."""
        if response.get("escalated") or response.get("violations"):
            return
        if response.get("intent") not in ("product",):
            return
        if len(self._entries) >= self.max_entries:
            self._entries.pop(0)
            self._embeddings.pop(0)
        self._entries.append({"question": question, "response": response,
                              "ts": time.time()})
        self._embeddings.append(self._embed(question))

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"entries": len(self._entries), "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 3) if total else 0.0}
