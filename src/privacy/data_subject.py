from datetime import datetime, timezone

from src.audit.logger import hash_user_id
from src.cache.response_cache import default_cache

DISCLOSURE_TEXT = (
    "This service uses an AI assistant to answer customer-support questions. "
    "Your message is processed by a large-language-model provider; PII detected in your "
    "input is masked before retrieval and unmasked only in the reply you receive. "
    "We retain operational logs for 90 days and security logs for one year."
)


def export_user_data(user_id: str) -> dict:
    return {
        "user_id_hash": hash_user_id(user_id),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "stored_records": {
            "conversation_history": [],
            "preferences": {},
            "cache_keys": [],
        },
    }


def delete_user_data(user_id: str) -> dict:
    cleared_cache = default_cache.size() > 0
    if cleared_cache:
        default_cache.clear()
    return {
        "user_id_hash": hash_user_id(user_id),
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "cleared": {
            "response_cache": cleared_cache,
            "conversation_history": False,
            "vector_store_personal_chunks": False,
        },
    }
