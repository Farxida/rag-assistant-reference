"""Tests for FastAPI endpoints (without LLM calls)."""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_chat_validation_empty_query():
    r = client.post("/chat", json={"query": ""})
    assert r.status_code == 422


def test_chat_validation_top_k_out_of_range():
    r = client.post("/chat", json={"query": "test", "top_k": 999})
    assert r.status_code == 422
