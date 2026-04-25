import pytest

from src.auth.context import ROLE_LEVELS, UserContext, anonymous_context


def test_anonymous_context_defaults_to_public():
    ctx = anonymous_context()
    assert ctx.tenant_id == "northwind-public"
    assert ctx.allowed_classifications() == ["public"]


def test_internal_role_unlocks_internal_classification():
    ctx = UserContext(user_id="alice", tenant_id="acme", roles=("internal",))
    assert ctx.allowed_classifications() == ["internal", "public"]


def test_restricted_role_unlocks_all_levels():
    ctx = UserContext(user_id="bob", tenant_id="acme", roles=("restricted",))
    assert ctx.allowed_classifications() == ["internal", "public", "restricted"]


def test_unknown_role_falls_back_to_public():
    ctx = UserContext(user_id="charlie", tenant_id="acme", roles=("guest",))
    assert ctx.allowed_classifications() == ["public"]


def test_multiple_roles_aggregate():
    ctx = UserContext(user_id="dana", tenant_id="acme", roles=("public", "internal"))
    assert ctx.allowed_classifications() == ["internal", "public"]


def test_user_context_is_immutable():
    ctx = UserContext(user_id="eve", tenant_id="acme", roles=("internal",))
    with pytest.raises(Exception):
        ctx.tenant_id = "other"


def test_can_see_blocks_other_tenant():
    visitor = UserContext(user_id="x", tenant_id="initech", roles=("public",))
    assert visitor.can_see("acme", "public") is False


def test_can_see_blocks_restricted_for_public_role():
    public_user = UserContext(user_id="x", tenant_id="acme", roles=("public",))
    assert public_user.can_see("acme", "restricted") is False


def test_can_see_allows_matching_tenant_and_class():
    staff = UserContext(user_id="x", tenant_id="acme", roles=("internal",))
    assert staff.can_see("acme", "internal") is True
    assert staff.can_see("acme", "public") is True


def test_can_see_blocks_unknown_classification():
    user = UserContext(user_id="x", tenant_id="acme", roles=("public",))
    assert user.can_see("acme", "secret") is False


def test_chroma_where_clause_includes_tenant_and_classifications():
    pytest.importorskip("chromadb")
    from src.ingestion.embedder import _build_where

    ctx = UserContext(user_id="x", tenant_id="acme", roles=("internal",))
    where = _build_where(ctx)
    assert where == {
        "$and": [
            {"tenant_id": "acme"},
            {"classification": {"$in": ["internal", "public"]}},
        ]
    }

