from pathlib import Path
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

@dataclass
class Chunk:
    text: str
    metadata: dict

def load_documents(data_dir: str) -> list[dict]:
    docs = []
    for md_file in sorted(Path(data_dir).glob("*.md")):
        docs.append({
            "text": md_file.read_text(encoding="utf-8"),
            "source": md_file.name,
        })
    print(f"Loaded {len(docs)} documents from {data_dir}")
    return docs

def chunk_documents(
    documents: list[dict],
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n---", "\n\n", "\n", ". ", " "],
        keep_separator=True,
    )

    chunks = []
    for doc in documents:
        for i, split in enumerate(splitter.split_text(doc["text"])):
            chunks.append(Chunk(
                text=split.strip(),
                metadata={
                    "source": doc["source"],
                    "chunk_id": f"{doc['source']}_{i}",
                    "chunk_index": i,
                },
            ))

    avg = sum(len(c.text) for c in chunks) // max(len(chunks), 1)
    print(f"Created {len(chunks)} chunks (avg size: {avg} chars)")
    return chunks

if __name__ == "__main__":
    docs = load_documents("data/raw")
    chunks = chunk_documents(docs)
    print(f"\nFirst 3 chunks:")
    for c in chunks[:3]:
        print(f"  [{c.metadata['source']}] {c.text[:100]}...")
