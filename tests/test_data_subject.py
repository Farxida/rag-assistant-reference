from src.privacy.data_subject import (
    DISCLOSURE_TEXT,
    delete_user_data,
    export_user_data,
)


def test_disclosure_text_mentions_ai_and_retention():
    assert "AI" in DISCLOSURE_TEXT or "language-model" in DISCLOSURE_TEXT.lower()
    assert "90 days" in DISCLOSURE_TEXT or "year" in DISCLOSURE_TEXT


def test_export_returns_hashed_user_id():
    payload = export_user_data("alice")
    assert payload["user_id_hash"]
    assert payload["user_id_hash"] != "alice"
    assert "exported_at" in payload


def test_export_lists_record_categories():
    payload = export_user_data("alice")
    assert "stored_records" in payload
    assert "conversation_history" in payload["stored_records"]


def test_delete_returns_hashed_user_id():
    payload = delete_user_data("alice")
    assert payload["user_id_hash"]
    assert "deleted_at" in payload


def test_delete_clears_response_cache():
    from src.cache.response_cache import default_cache

    default_cache.set("anything", "northwind-public", {"answer": "x"})
    assert default_cache.size() >= 1
    delete_user_data("alice")
    assert default_cache.size() == 0


def test_delete_payload_lists_scope():
    payload = delete_user_data("alice")
    assert "cleared" in payload
    assert "response_cache" in payload["cleared"]
