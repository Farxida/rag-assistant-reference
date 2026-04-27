import hashlib
import hmac
import os
import re

import structlog

DEFAULT_SALT = "rag-reference-dev-salt"

CANARY = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}"),
    "uk_phone": re.compile(r"\+44\s?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "uk_postcode": re.compile(r"\b[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}\b"),
    "uk_nino": re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[A-D]?\b"),
}


def _salt() -> bytes:
    return os.environ.get("AUDIT_HMAC_SECRET", DEFAULT_SALT).encode()


def hash_user_id(user_id: str) -> str:
    if not user_id:
        return ""
    return hmac.new(_salt(), user_id.encode(), hashlib.sha256).hexdigest()[:16]


def pii_canary_check(text: str) -> list[str]:
    if not text:
        return []
    return [name for name, p in CANARY.items() if p.search(text)]


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    cache_logger_on_first_use=True,
)
_log = structlog.get_logger("rag.audit")


def log_query(
    user_id, masked_query, chunk_ids, response_id, latency_ms,
    tokens_in=None, tokens_out=None, pii_detected=None,
    suspicious_output=False, tenant_id=None,
):
    _log.info(
        "rag_query",
        user_hash=hash_user_id(user_id),
        tenant=tenant_id,
        query_masked=masked_query,
        chunks=chunk_ids,
        response_id=response_id,
        latency_ms=round(latency_ms, 2),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        pii_entities=pii_detected or [],
        suspicious_output=suspicious_output,
        canary_hits=pii_canary_check(masked_query),
    )
