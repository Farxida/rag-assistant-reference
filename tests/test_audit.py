import io
import json
import logging
import os

import pytest
import structlog

from src.audit.logger import hash_user_id, log_query, pii_canary_check


def test_hash_is_deterministic():
    h1 = hash_user_id("alice")
    h2 = hash_user_id("alice")
    assert h1 == h2


def test_hash_is_short_and_hex():
    h = hash_user_id("alice")
    assert len(h) == 16
    assert all(c in "0123456789abcdef" for c in h)


def test_different_users_get_different_hashes():
    assert hash_user_id("alice") != hash_user_id("bob")


def test_hash_changes_with_salt(monkeypatch):
    monkeypatch.setenv("AUDIT_HMAC_SECRET", "salt-one")
    h1 = hash_user_id("alice")
    monkeypatch.setenv("AUDIT_HMAC_SECRET", "salt-two")
    h2 = hash_user_id("alice")
    assert h1 != h2


def test_hash_empty_returns_empty():
    assert hash_user_id("") == ""


def test_canary_detects_email():
    assert "email" in pii_canary_check("Contact alice@example.com today")


def test_canary_detects_uk_phone():
    assert "uk_phone" in pii_canary_check("Call +44 20 7946 0958")


def test_canary_detects_credit_card():
    assert "credit_card" in pii_canary_check("Card 4111 1111 1111 1111")


def test_canary_clean_text_returns_empty():
    assert pii_canary_check("The Business plan costs $299 per month") == []


def test_canary_handles_empty():
    assert pii_canary_check("") == []
    assert pii_canary_check(None) == []


def _last_event(captured: str) -> dict:
    line = captured.strip().splitlines()[-1]
    return json.loads(line)


def test_log_query_emits_required_fields(capsys):
    log_query(
        user_id="alice",
        masked_query="What is the [EMAIL_ADDRESS_xxx] price?",
        chunk_ids=["faq.md_0", "pricing.md_3"],
        response_id="abc123",
        latency_ms=42.7,
        tokens_in=120,
        tokens_out=85,
        pii_detected=["EMAIL_ADDRESS"],
        suspicious_output=False,
        tenant_id="northwind-public",
    )
    out = capsys.readouterr().out
    event = _last_event(out)
    assert event["event"] == "rag_query"
    assert event["response_id"] == "abc123"
    assert event["chunks"] == ["faq.md_0", "pricing.md_3"]
    assert event["pii_entities"] == ["EMAIL_ADDRESS"]
    assert event["tenant"] == "northwind-public"
    assert event["user_hash"]
    assert "raw_query" not in event


def test_log_query_canary_flags_unmasked_pii(capsys):
    log_query(
        user_id="alice",
        masked_query="Please email me at john@example.com",
        chunk_ids=["faq.md_0"],
        response_id="leak-xyz",
        latency_ms=10.0,
    )
    event = _last_event(capsys.readouterr().out)
    assert event["response_id"] == "leak-xyz"
    assert "email" in event["canary_hits"]


def test_log_query_clean_query_no_canary(capsys):
    log_query(
        user_id="alice",
        masked_query="What does the Business plan include?",
        chunk_ids=[],
        response_id="clean-1",
        latency_ms=5.0,
    )
    event = _last_event(capsys.readouterr().out)
    assert event["canary_hits"] == []
