# RAG Customer Support Assistant

![Tests](https://github.com/Farxida/rag-assistant-reference/actions/workflows/tests.yml/badge.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)

> Retrieval-Augmented Generation system for customer support over a domain knowledge base. Hybrid retrieval (BM25 + dense embeddings), cross-encoder reranking, and an evaluation pipeline with LLM-as-judge. Built and measured on a SaaS documentation corpus (Northwind Cloud — fictional company for reproducibility).

---

## Highlights

- **Real measured evaluation**: 30-question test set, **Recall@5 = 96.7%**, **Correctness = 93.3%** (LLM-as-judge), avg total latency **1.1 s**
- **Production architecture**: hybrid retrieval (BM25 + dense) → cross-encoder rerank → calibrated generation
- **Ablation study**: vector-only vs hybrid vs hybrid+rerank — recall and latency trade-offs documented
- **End-to-end runnable**: `python demo.py "your question"` works after a single ingestion command
- **REST API** (FastAPI) + **CLI** entry points
- **12 unit tests** passing in CI

---

## Quick Results

![Evaluation summary](assets/eval_summary.png)

Per-category breakdown across 12 question types:

![Per-category evaluation](assets/eval_by_category.png)

---

## Architecture

```mermaid
flowchart TB
    subgraph ingest["📥 Ingestion (offline)"]
        A1[Markdown documents] --> A2["RecursiveCharacter<br/>chunker (512/50)"]
        A2 --> A3["all-MiniLM-L6-v2<br/>(384-dim embeddings)"]
        A3 --> A4[(ChromaDB<br/>cosine similarity)]
    end

    subgraph query["🔍 Query (online)"]
        B1[User question] --> B2{Hybrid retrieval}
        B2 --> B3["Dense vector<br/>top-20"]
        B2 --> B4["BM25<br/>top-20"]
        B3 --> B5[RRF fusion<br/>k=60]
        B4 --> B5
        B5 --> B6["Cross-encoder rerank<br/>ms-marco-MiniLM-L-6-v2"]
        B6 --> B7["Top-5 chunks"]
        B7 --> B8["Llama 3.3 70B<br/>via Groq"]
        B8 --> B9[Answer + sources]
    end

    A4 -.-> B3

    subgraph eval["📊 Evaluation"]
        C1[30 Q&A test set] --> C2[Retrieval eval<br/>Recall@5]
        C1 --> C3[Generation eval]
        C3 --> C4[LLM-as-judge<br/>correctness 0.0–1.0]
    end
```

---

## Stack

| Layer | Tool / Model |
|---|---|
| **LLM** | Llama 3.3 70B via [Groq](https://groq.com) (primary), Gemini 2.0 Flash (fallback) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| **Vector DB** | [ChromaDB](https://www.trychroma.com/) (persistent, cosine similarity) |
| **Lexical retrieval** | BM25 (`rank-bm25`) |
| **Reranker** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **Chunking** | `langchain-text-splitters` RecursiveCharacterTextSplitter |
| **Agent** | [LangGraph](https://langchain-ai.github.io/langgraph/) (graph + tools — backend) |
| **API** | FastAPI + Uvicorn |
| **Eval** | Custom retrieval + LLM-as-judge pipeline |
| **Testing** | pytest |

---

## Pipeline

The system runs as two phases:

**Ingestion (offline, ~15 sec for the demo corpus):**

1. Load markdown documents from `data/raw/`
2. Hierarchical chunking (chunk size 512, overlap 50) — splits on headers first, then paragraphs, sentences, words
3. Embed each chunk with `all-MiniLM-L6-v2` (384 dimensions)
4. Persist embeddings + metadata in ChromaDB

**Query (online, ~1.1 sec end-to-end):**

1. **Hybrid retrieval** — dense vector search + BM25 in parallel, fused via Reciprocal Rank Fusion (`score(d) = Σ weight_i / (k + rank_i(d))`, `k=60`). Top-20 candidates.
2. **Cross-encoder reranking** — re-scores each (query, chunk) pair with a fine-tuned cross-encoder. Selects top-5.
3. **Generation** — Llama 3.3 70B receives the question + retrieved context and produces the answer with citations.
4. **Output** — answer text + list of source documents.

---

## Evaluation Methodology

**Test set:** 30 questions across 12 categories (`api`, `billing`, `pricing`, `security`, `sla`, `integrations`, `migration`, `policy`, `getting_started`, `limits`, `technical`, `troubleshooting`). Each question has a ground-truth answer and an expected source document.

**Metrics:**
- **Recall@5** — does the expected source document appear in the top-5 retrieved chunks?
- **Correctness** (0.0–1.0) — Llama 3.3 70B judges each generated answer against the ground truth on a fixed rubric.
- **Latency** — end-to-end time from question to answer (retrieval + generation).

The full pipeline including the LLM judge is reproducible: `python -m src.evaluation.evaluate full`. Test set is committed at `data/eval/test_set.json`. Reports are written to `data/eval/report.json`.

### Ablation: how much does each component contribute?

![Ablation](assets/ablation.png)

| Configuration | Recall@5 | Avg retrieval | Notes |
|---|---:|---:|---|
| Vector only (dense embeddings) | **100.0%** | 9 ms | Sufficient on this clean small corpus |
| + BM25 hybrid (RRF fusion) | 96.7% | 7 ms | Adds keyword precision; slightly noisier on small N |
| + Cross-encoder reranker | 96.7% | 310 ms | Reorders for relevance; pays in latency |

**Honest finding:** on a 100-chunk well-curated corpus, dense vector search alone is sufficient. Hybrid and reranking show their value on larger, noisier production corpora where keyword matching catches what semantic search misses (e.g., exact product names, error codes, version numbers). The reference architecture keeps the full stack because that was the production configuration; for this synthetic eval it's a documented trade-off.

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set GROQ_API_KEY (free tier at https://console.groq.com)
cp .env.example .env
# edit .env to add your key

# 3. Build the knowledge base (loads markdown → chunks → ChromaDB)
python -m src.ingestion.build_knowledge_base

# 4. Ask a question
python demo.py "How much does the Business plan cost?"
```

Real output captured from the running pipeline:

```
$ python demo.py "What is the maximum file upload size on Business plan?"

[hybrid+rerank] 5 chunks:
  [limits_and_quotas.md] (rerank_score=8.214) | Single file upload | 100 MB | 1 GB | 10 GB | 10 GB | ...
  [faq.md]               (rerank_score=2.145) Q: What's the maximum query result size? A: 100K rows for inli...
  [getting_started.md]   (rerank_score=1.872) For files (CSV, JSON, Parquet), use Data → Upload and drag-and-drop. Files up to 10 GB ...
  ...

Q: What is the maximum file upload size on Business plan?

A: The maximum single file upload size on the Business plan is 10 GB. You can upload files
   up to this size using the Data → Upload feature with drag-and-drop.

Sources: limits_and_quotas.md, getting_started.md, faq.md
```

### REST API

```bash
uvicorn src.api.main:app --port 8000
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What payment methods do you accept?"}'
```

### Docker

```bash
docker-compose up
```

Builds the image, runs ingestion at build-time, and exposes the API on `:8000` with a health-check.

---

## Cost Analysis

Per-1K-queries cost on the demo corpus (100 chunks, 5 chunks per query, ~500-token answers):

| LLM (provider) | $/1K queries | Latency p50 | Notes |
|---|---:|---:|---|
| **Llama 3.3 70B (Groq)** | **~$0.40** | **1.1 s** | Production choice. Free tier available. |
| Llama 3.1 8B (Groq) | $0.05 | 0.7 s | 8× cheaper, ~5 pp lower correctness on this eval |
| GPT-4o-mini (OpenAI) | $0.42 | 1.6 s | Comparable cost, slower |
| GPT-4o (OpenAI) | $4.20 | 2.4 s | 10× cost; not justified at this corpus quality |
| Claude 3.5 Haiku (Anthropic) | $1.40 | 1.4 s | Mid-tier alternative |

Embedding + reranker run locally on CPU — zero per-query LLM-side cost. ChromaDB has no per-query fee.

**Decision in the architecture**: Llama 3.3 70B via Groq for cost-quality optimum at this corpus size. For >10× larger corpora with stricter quality bars, consider Claude or GPT-4o on a tier-routing middleware (cheap model for simple lookups, expensive model for synthesis).

---

## Reproduce the Evaluation

```bash
# Retrieval-only eval (fast, no LLM calls — ~30 sec)
python -m src.evaluation.evaluate retrieval

# Ablation across 3 retrieval configurations
python -m src.evaluation.evaluate ablation

# Full eval (retrieval + generation + LLM judge — ~2 min)
python -m src.evaluation.evaluate full
```

Reports are written to `data/eval/report.json` (full eval) or `data/eval/ablation.json`.

---

## Project Structure

```
.
├── demo.py                          # CLI entry point
├── data/
│   ├── raw/                         # 14 markdown documents (synthetic SaaS docs)
│   ├── eval/test_set.json           # 30-question test set with ground truths
│   └── chroma_db/                   # built locally, gitignored
├── src/
│   ├── ingestion/
│   │   ├── chunker.py               # recursive markdown chunking
│   │   ├── embedder.py              # ChromaDB + sentence-transformers
│   │   └── build_knowledge_base.py  # full ingestion pipeline
│   ├── retrieval/
│   │   ├── hybrid.py                # BM25 + dense + RRF fusion
│   │   ├── reranker.py              # cross-encoder reranking
│   │   └── rag.py                   # full RAG: query → context → LLM
│   ├── evaluation/
│   │   └── evaluate.py              # retrieval / ablation / full eval modes
│   └── api/
│       └── main.py                  # FastAPI service
├── tests/                           # 12 unit tests
└── assets/                          # generated charts for this README
```

---

## License

MIT
