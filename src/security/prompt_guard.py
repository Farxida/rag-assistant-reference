import re

SUSPICIOUS_PATTERNS = [
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"ignore\s+(?:all|previous|prior|above)", re.IGNORECASE),
    re.compile(r"\byou are now\b", re.IGNORECASE),
    re.compile(r"\bact as\b", re.IGNORECASE),
    re.compile(r"\bdeveloper mode\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"BEGIN\s+SYSTEM", re.IGNORECASE),
    re.compile(r"<\s*tool[_-]?call\s*>", re.IGNORECASE),
]


def wrap_context_chunk(text: str, source: str, chunk_id: str) -> str:
    safe = text.replace("<doc", "&lt;doc").replace("</doc>", "&lt;/doc&gt;")
    return f'<doc id="{chunk_id}" source="{source}">\n{safe}\n</doc>'


def is_suspicious_output(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in SUSPICIOUS_PATTERNS)
