import json
import os
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv
from groq import Groq

from src.retrieval.rag import RAGPipeline
from src.retrieval.hybrid import hybrid_search
from src.retrieval.reranker import rerank
from src.ingestion.embedder import search as vector_search

load_dotenv()

@dataclass
class EvalResult:
    question_id: int
    question: str
    category: str
    source_recall: float
    retrieved_sources: list[str] = field(default_factory=list)
    expected_source: str = ""
    answer: str = ""
    ground_truth: str = ""
    correctness: float = 0.0
    retrieval_time_ms: float = 0.0
    total_time_ms: float = 0.0

def load_test_set(path: str = "data/eval/test_set.json") -> list[dict]:
    with open(path) as f:
        return json.load(f)

def evaluate_retrieval(
    test_set: list[dict],
    top_k: int = 5,
    use_hybrid: bool = True,
    use_reranker: bool = True,
) -> list[EvalResult]:
    results = []
    for item in test_set:
        t0 = time.time()

        if use_hybrid:
            candidates = hybrid_search(item["question"], top_k=20)
            if use_reranker:
                retrieved = rerank(item["question"], candidates, top_k=top_k)
            else:
                retrieved = candidates[:top_k]
        else:
            retrieved = vector_search(item["question"], top_k=top_k)

        retrieval_ms = (time.time() - t0) * 1000

        retrieved_sources = list(set(r["source"] for r in retrieved))
        expected = item["expected_source"]
        recall = 1.0 if expected in retrieved_sources else 0.0

        results.append(EvalResult(
            question_id=item["id"],
            question=item["question"],
            category=item["category"],
            source_recall=recall,
            retrieved_sources=retrieved_sources,
            expected_source=expected,
            ground_truth=item["ground_truth"],
            retrieval_time_ms=retrieval_ms,
        ))
    return results

def evaluate_full(
    test_set: list[dict],
    rag: RAGPipeline,
    sleep_between: float = 1.0,
) -> list[EvalResult]:
    results = []
    for i, item in enumerate(test_set):
        t0 = time.time()
        rag_result = rag.query(item["question"])
        total_ms = (time.time() - t0) * 1000

        retrieved_sources = rag_result["sources"]
        expected = item["expected_source"]
        recall = 1.0 if expected in retrieved_sources else 0.0

        results.append(EvalResult(
            question_id=item["id"],
            question=item["question"],
            category=item["category"],
            source_recall=recall,
            retrieved_sources=retrieved_sources,
            expected_source=expected,
            ground_truth=item["ground_truth"],
            answer=rag_result["answer"],
            total_time_ms=total_ms,
        ))

        if (i + 1) % 5 == 0:
            print(f"  Progress: {i+1}/{len(test_set)}")
        if i < len(test_set) - 1 and sleep_between > 0:
            time.sleep(sleep_between)

    return results

def judge_correctness(results: list[EvalResult], sleep_between: float = 1.0) -> list[EvalResult]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY required for LLM judge")

    client = Groq(api_key=api_key)

    template = """You are an evaluation judge for a customer support bot.

Compare the bot's answer to the ground-truth answer.

Ground truth: {gt}

Bot's answer: {answer}

Rate correctness from 0.0 to 1.0:
- 1.0: fully correct, covers all key points
- 0.7-0.9: mostly correct, minor omissions
- 0.4-0.6: partially correct, missing important details
- 0.1-0.3: mostly wrong or misleading
- 0.0: completely wrong or refused to answer

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

    for i, r in enumerate(results):
        if not r.answer:
            continue
        prompt = template.format(gt=r.ground_truth, answer=r.answer)

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            score = float(response.choices[0].message.content.strip())
            r.correctness = min(max(score, 0.0), 1.0)
        except Exception as e:
            print(f"  Q{r.question_id} judge failed: {e}")
            r.correctness = 0.0

        if (i + 1) % 10 == 0:
            print(f"  Judge progress: {i+1}/{len(results)}")
        if i < len(results) - 1 and sleep_between > 0:
            time.sleep(sleep_between)

    return results

def aggregate(results: list[EvalResult]) -> dict:
    n = len(results)
    return {
        "total": n,
        "recall_at_5": sum(r.source_recall for r in results) / max(n, 1),
        "correctness": sum(r.correctness for r in results) / max(n, 1),
        "avg_retrieval_ms": sum(r.retrieval_time_ms for r in results) / max(n, 1),
        "avg_total_ms": sum(r.total_time_ms for r in results) / max(n, 1) if any(r.total_time_ms for r in results) else 0,
    }

def print_report(results: list[EvalResult], title: str = "Evaluation Report"):
    agg = aggregate(results)
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}\n")
    print(f"  Total questions:   {agg['total']}")
    print(f"  Recall@5:          {agg['recall_at_5']:.1%}")
    if agg["correctness"] > 0:
        print(f"  Correctness:       {agg['correctness']:.1%}")
    if agg["avg_retrieval_ms"] > 0:
        print(f"  Avg retrieval:     {agg['avg_retrieval_ms']:.0f} ms")
    if agg["avg_total_ms"] > 0:
        print(f"  Avg total:         {agg['avg_total_ms']:.0f} ms")

    cats = sorted(set(r.category for r in results))
    print(f"\n  {'Category':<18} {'N':>3} {'Recall':>8} {'Correct':>8}")
    print(f"  {'-'*18} {'-'*3} {'-'*8} {'-'*8}")
    for c in cats:
        cr = [r for r in results if r.category == c]
        n = len(cr)
        rec = sum(r.source_recall for r in cr) / n
        cor = sum(r.correctness for r in cr) / n if any(r.correctness for r in cr) else 0
        print(f"  {c:<18} {n:>3} {rec:>7.0%} {cor:>7.0%}")

    failed = [r for r in results if r.source_recall == 0]
    if failed:
        print(f"\n  Failed retrieval ({len(failed)}):")
        for r in failed[:5]:
            print(f"    Q{r.question_id}: {r.question}")
            print(f"      expected: {r.expected_source}")
            print(f"      got:      {r.retrieved_sources}")

    print(f"\n{'=' * 60}\n")

def save_report(results: list[EvalResult], path: str = "data/eval/report.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metrics": aggregate(results),
        "details": [asdict(r) for r in results],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Report saved: {path}")

if __name__ == "__main__":
    import sys

    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")

    mode = sys.argv[1] if len(sys.argv) > 1 else "retrieval"

    if mode == "retrieval":
        print("\nMode: retrieval-only (no LLM)\n")
        results = evaluate_retrieval(test_set)
        print_report(results, "Retrieval Evaluation")
        save_report(results, "data/eval/report_retrieval.json")

    elif mode == "ablation":
        print("\nMode: ablation (vector vs hybrid vs hybrid+rerank)\n")
        configs = [
            ("vector_only",   dict(use_hybrid=False, use_reranker=False)),
            ("hybrid",        dict(use_hybrid=True,  use_reranker=False)),
            ("hybrid+rerank", dict(use_hybrid=True,  use_reranker=True)),
        ]
        all_results = {}
        for name, kwargs in configs:
            print(f"\n>>> {name}")
            res = evaluate_retrieval(test_set, **kwargs)
            all_results[name] = aggregate(res)
            print_report(res, f"Retrieval — {name}")

        with open("data/eval/ablation.json", "w") as f:
            json.dump(all_results, f, indent=2)
        print("Ablation results saved: data/eval/ablation.json")

    elif mode == "full":
        print("\nMode: full (retrieval + generation + LLM judge)\n")
        rag = RAGPipeline()
        results = evaluate_full(test_set, rag, sleep_between=1.0)
        results = judge_correctness(results, sleep_between=1.0)
        print_report(results, "Full Evaluation")
        save_report(results, "data/eval/report.json")
