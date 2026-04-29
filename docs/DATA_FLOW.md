# Data flow

This is a quick map of how a query flows through the system and where PII can appear.

## Request path

1. User hits `POST /chat` over HTTPS.
2. `UserContext` is built from the auth layer (anonymous fallback in this repo).
3. `PIIShield` masks PII in the query; the mapping lives only in the request scope.
4. Hybrid retrieval runs against ChromaDB and BM25, both filtered by `tenant_id` and `classification`.
5. Top-5 chunks are wrapped in `<doc>` tags and passed to the LLM.
6. The answer is unmasked, scanned for suspicious patterns, and returned.
7. `log_query` writes a JSON event with HMAC-hashed user id, masked query, chunk ids, latency, token counts, and any PII canary hits.

## PII surface

| Stage | Risk | Control |
|---|---|---|
| User query in transit | TLS at the reverse proxy |
| Vector store | Synthetic corpus only here. Production uses pre-ingestion `PIIShield.mask` for documents. |
| BM25 index | Same as vector store. |
| Prompt to LLM | Chunks are wrapped in `<doc>` tags; PII is masked by the shield. |
| LLM response | The shield only un-replaces tokens it created. The canary regex flags anything else. |
| Audit log | Only HMAC-hashed user id and masked query are logged. |

## Encryption (production targets)

- **In transit**: TLS at the proxy (Caddy / nginx + Let's Encrypt, or AWS ALB + ACM).
- **In transit, API → LLM**: TLS via the SDK (Groq / Gemini / Anthropic).
- **At rest**: encrypted volume for ChromaDB (AWS EBS + KMS or LUKS).
- **At rest, application-level**: `cryptography.fernet` for stored conversation history if added.

## Secrets

`.env` is gitignored. Keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `AUDIT_HMAC_SECRET`) live in a managed secret store in production with 90-day rotation. `gitleaks` runs in pre-commit and CI.
