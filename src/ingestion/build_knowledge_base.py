from src.ingestion.chunker import load_documents, chunk_documents
from src.ingestion.embedder import create_collection

def build(data_dir: str = "data/raw", reset: bool = True) -> None:
    print(f"=== Building knowledge base from {data_dir} ===\n")

    docs = load_documents(data_dir)
    chunks = chunk_documents(docs)
    create_collection(chunks, reset=reset)

    print("\nDone.")

if __name__ == "__main__":
    build()
