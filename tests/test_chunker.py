"""Tests for chunker."""

import tempfile
from pathlib import Path

from src.ingestion.chunker import load_documents, chunk_documents, Chunk


def _write_md(dir_path: Path, name: str, content: str) -> None:
    (dir_path / name).write_text(content)


def test_load_documents_reads_all_md():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        _write_md(p, "a.md", "# A\nContent A.")
        _write_md(p, "b.md", "# B\nContent B.")

        docs = load_documents(str(p))
        assert len(docs) == 2
        assert {d["source"] for d in docs} == {"a.md", "b.md"}


def test_chunk_documents_produces_chunks():
    docs = [{"text": "# Header\n\nFirst paragraph.\n\nSecond paragraph.", "source": "x.md"}]
    chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=10)
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.metadata["source"] == "x.md" for c in chunks)


def test_chunk_overlap_preserves_context():
    long_text = "Sentence one. " * 50
    docs = [{"text": long_text, "source": "long.md"}]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 1


def test_chunks_have_unique_ids():
    docs = [
        {"text": "alpha", "source": "a.md"},
        {"text": "beta",  "source": "b.md"},
    ]
    chunks = chunk_documents(docs)
    ids = [c.metadata["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
