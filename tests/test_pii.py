from src.privacy.pii import PIIShield


def _has(shield, entity):
    return any(t.startswith(f"[{entity}_") for t in shield.mapping)


def test_mask_email():
    s = PIIShield()
    out = s.mask("Please contact me at john.smith@example.com")
    assert "john.smith@example.com" not in out
    assert _has(s, "EMAIL_ADDRESS")


def test_mask_uk_phone():
    s = PIIShield()
    out = s.mask("Call me on +44 20 7946 0958")
    assert "+44 20 7946 0958" not in out
    assert _has(s, "PHONE_NUMBER")


def test_mask_uk_postcode():
    s = PIIShield()
    out = s.mask("My address is 10 Downing Street, SW1A 2AA")
    assert "SW1A 2AA" not in out
    assert _has(s, "UK_POSTCODE")


def test_mask_uk_nino():
    s = PIIShield()
    out = s.mask("My NI number is AB123456C")
    assert "AB123456C" not in out
    assert _has(s, "UK_NINO")


def test_mask_credit_card():
    s = PIIShield()
    out = s.mask("Card 4111 1111 1111 1111 expires 12/25")
    assert "4111 1111 1111 1111" not in out
    assert _has(s, "CREDIT_CARD")


def test_does_not_mask_company_names():
    s = PIIShield()
    out = s.mask("Northwind Cloud is a SaaS analytics platform")
    assert "Northwind Cloud" in out or s.mapping == {}


def test_does_not_mask_currency():
    s = PIIShield()
    out = s.mask("The Business plan costs $299 per month")
    assert "$299" in out


def test_roundtrip_preserves_text():
    s = PIIShield()
    original = "Email me at alice@northwind.cloud or call +44 20 7946 0958"
    assert s.unmask(s.mask(original)) == original


def test_multiple_entities_in_one_text():
    s = PIIShield()
    out = s.mask("Contact John Doe at john@example.com or +44 20 7946 0958, postcode SW1A 1AA")
    for needle in ("john@example.com", "+44 20 7946 0958", "SW1A 1AA"):
        assert needle not in out


def test_empty_text():
    s = PIIShield()
    assert s.mask("") == ""
    assert s.unmask("") == ""
