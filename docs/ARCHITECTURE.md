# Architecture

## Modules

```
src/
  audit/        structured logging + PII canary
  auth/         UserContext + classification ACLs
  cache/        TTL response cache
  ingestion/    chunker + ChromaDB embedder
  privacy/      Presidio PII shield + GDPR endpoints
  retrieval/    hybrid + cross-encoder rerank + RAG pipeline
  security/     prompt-injection defense
  evaluation/   retrieval / ablation / full / adversarial / gate modes
  api/          FastAPI service (rate-limited, /metrics)
```

## Request lifecycle (`POST /chat`)

1. Auth layer builds a `UserContext` (tenant + roles).
2. `PIIShield` masks PII in the query.
3. `hybrid_search` queries ChromaDB and BM25 with the same metadata filter (`tenant_id`, allowed classifications).
4. Cross-encoder reranks top-20 candidates → top-5.
5. `build_context` wraps chunks in `<doc>` tags and passes them to the LLM with retry-with-backoff.
6. `unmask` restores PII in the answer; `is_suspicious_output` flags known leak patterns.
7. `log_query` emits a JSON audit event.
8. Response is returned with `answer`, `sources`, `latency_ms`, `response_id`.

## Production deployment (target)

- **Region**: AWS `eu-west-2` (London) for UK-GDPR data residency.
- **LLM**: Anthropic via Bedrock to keep traffic inside the AWS account.
- **Network**: API in private subnet behind ALB with WAF; egress restricted to the LLM endpoint.
- **Secrets**: AWS Secrets Manager with 90-day rotation.
- **Storage**: ChromaDB on encrypted EBS.
- **Observability**: Prometheus `/metrics` (`prometheus-fastapi-instrumentator`), CloudWatch for logs.
- **CI/CD**: pytest + `gitleaks` + `bandit` + `pip-audit` per PR; eval `gate` mode blocks merges on `>5pp` correctness drop.
