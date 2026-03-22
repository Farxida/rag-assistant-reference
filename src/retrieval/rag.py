import os
import time
from dotenv import load_dotenv
from groq import Groq

from src.ingestion.embedder import search as vector_search
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import rerank

load_dotenv()

SYSTEM_PROMPT = """You are a customer support assistant for Northwind Cloud, a cloud analytics platform.

Rules:
- Answer ONLY based on the provided context. Do not make up information.
- Be concise and helpful. Keep answers under 150 words.
- Use professional, friendly tone.
- For complaints or complex issues, suggest contacting support@northwind.cloud.

If the answer is in the context but requires reasoning, answer confidently based on the context.
Only say "I don't have that information" as a last resort when the topic is covered but the specific answer truly isn't in the context.

NEVER:
- Promise specific delivery dates or commitments
- Discuss internal company matters
- Offer discounts not documented in the knowledge base"""

def build_context(results: list[dict]) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {r['source']}]\n{r['text']}" for r in results
    )

def build_prompt(question: str, context: str) -> str:
    return f"""Context from Northwind Cloud knowledge base:

{context}

---

Customer question: {question}

Please answer the customer's question based on the context above."""

class RAGPipeline:
    def __init__(
        self,
        model_name: str = "llama-3.3-70b-versatile",
        top_k: int = 5,
        use_hybrid: bool = True,
        use_reranker: bool = True,
    ):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.top_k = top_k
        self.use_hybrid = use_hybrid
        self.use_reranker = use_reranker

    def query(self, question: str, verbose: bool = False) -> dict:
        if self.use_hybrid:
            candidates = hybrid_search(question, top_k=20)
            if self.use_reranker:
                results = rerank(question, candidates, top_k=self.top_k)
            else:
                results = candidates[:self.top_k]
        else:
            results = vector_search(question, top_k=self.top_k)

        if verbose:
            mode = "hybrid+rerank" if self.use_hybrid and self.use_reranker else "vector"
            print(f"\n[{mode}] {len(results)} chunks:")
            for r in results:
                key = "rerank_score" if "rerank_score" in r else "score" if "score" in r else "distance"
                print(f"  [{r['source']}] ({key}={r.get(key, 0):.3f}) {r['text'][:80]}...")

        context = build_context(results)
        prompt = build_prompt(question, context)
        answer = self._generate(prompt)
        sources = list(set(r["source"] for r in results))

        return {"answer": answer, "sources": sources, "chunks": results, "question": question}

    def _generate(self, prompt: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                )
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    wait = 3 * (attempt + 1)
                    print(f"  Rate limit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
        return "Service temporarily busy. Please try again."

if __name__ == "__main__":
    rag = RAGPipeline()
    result = rag.query("How much is the Business plan?", verbose=True)
    print(f"\nAnswer:\n{result['answer']}")
    print(f"Sources: {result['sources']}")
