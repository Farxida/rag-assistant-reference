import uuid
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer

UK_POSTCODE = PatternRecognizer(
    supported_entity="UK_POSTCODE",
    patterns=[Pattern("uk_postcode", r"\b[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}\b", 0.85)],
    supported_language="en",
)

UK_NINO = PatternRecognizer(
    supported_entity="UK_NINO",
    patterns=[Pattern("uk_nino", r"\b[A-CEGHJ-PR-TW-Z]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[A-D]?\b", 0.85)],
    supported_language="en",
)

UK_NHS = PatternRecognizer(
    supported_entity="UK_NHS",
    patterns=[Pattern("uk_nhs", r"\b[0-9]{3}\s?[0-9]{3}\s?[0-9]{4}\b", 0.4)],
    supported_language="en",
)

DEFAULT_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
    "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS",
    "UK_POSTCODE", "UK_NINO", "UK_NHS",
]


@lru_cache(maxsize=1)
def _analyzer():
    a = AnalyzerEngine()
    a.registry.add_recognizer(UK_POSTCODE)
    a.registry.add_recognizer(UK_NINO)
    a.registry.add_recognizer(UK_NHS)
    return a


def _drop_overlaps(results):
    out = []
    for r in sorted(results, key=lambda r: (-(r.end - r.start), -r.score)):
        if not any(not (r.end <= a.start or r.start >= a.end) for a in out):
            out.append(r)
    return out


class PIIShield:
    def __init__(self, entities=None):
        self.entities = entities or DEFAULT_ENTITIES
        self.mapping: dict[str, str] = {}

    def mask(self, text: str) -> str:
        if not text:
            return text
        results = _analyzer().analyze(text=text, language="en", entities=self.entities)
        results = sorted(_drop_overlaps(results), key=lambda r: -r.start)
        out = text
        for r in results:
            token = f"[{r.entity_type}_{uuid.uuid4().hex[:6]}]"
            self.mapping[token] = text[r.start:r.end]
            out = out[:r.start] + token + out[r.end:]
        return out

    def unmask(self, text: str) -> str:
        if not text:
            return text
        for token, original in self.mapping.items():
            text = text.replace(token, original)
        return text

    def detected_entities(self) -> list[str]:
        return [t.split("_")[0].lstrip("[") for t in self.mapping]
