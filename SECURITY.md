# Security

## Reporting a vulnerability

Email `alexgrom465@gmail.com` with the subject `[security] rag-assistant-reference`. Please give a 90-day disclosure window before publishing details.

## What's implemented

- **PII masking** — `src/privacy/pii.py` masks emails, phones, postcodes, NINO, NHS, credit cards, IBAN before retrieval and unmasks only in the final answer.
- **Tenant + classification RBAC** — `src/auth/context.py` + filters in `src/ingestion/embedder.py` and `src/retrieval/hybrid.py`. Filters apply to ChromaDB and BM25 in two independent paths.
- **Prompt-injection defense** — chunks wrapped in `<doc>` tags and the system prompt forbids following instructions inside tags. `is_suspicious_output` flags known leak patterns.
- **Audit log** — `structlog` JSON events with HMAC-hashed user ids; canary regex flags PII that slipped through masking.
- **GDPR endpoints** — `DELETE /privacy/user/{id}`, `GET /privacy/user/{id}/export`, `GET /disclosure`.
- **Rate limiting** — `slowapi` at `100/day, 10/minute` per IP on `/chat`.
- **Adversarial eval + regression gate** — `python -m src.evaluation.evaluate adversarial` plus `gate` mode that fails CI on `>5pp` correctness drop.
- **Secret hygiene** — `.gitleaks.toml` with custom rules for Groq / Gemini / Anthropic keys, run in pre-commit and CI.
- **Static analysis** — `bandit` and `pip-audit` in CI.

## GDPR notes

User ids are HMAC-pseudonymised with a salt held outside the repo (`AUDIT_HMAC_SECRET`). Operational logs are kept 90 days, security logs one year. Delete and export endpoints cover Articles 17 and 20.

## Tested attack patterns

`tests/test_prompt_guard.py` covers `ignore previous`, system-prompt exfiltration, role hijacks (`You are now ...`), `developer mode` jailbreaks, and `<tool_call>` injections. For broader red-team coverage, [garak](https://github.com/NVIDIA/garak) is the recommended scanner.

## Production gaps

This repo is a reference implementation. Production additionally needs: TLS at the proxy, encrypted storage (KMS or LUKS), real auth provider (`UserContext` is set by your JWT middleware), and a managed secret store (Vault / AWS Secrets Manager) with 90-day key rotation.
