import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pathlib import Path

from src.auth.context import UserContext, anonymous_context
from src.ingestion.chunker import Chunk

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_FN = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

CHROMA_PATH = Path("data/chroma_db")
COLLECTION_NAME = "knowledge_base"

def get_client() -> chromadb.PersistentClient:
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))

def create_collection(chunks: list[Chunk], reset: bool = False) -> chromadb.Collection:
    client = get_client()

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=EMBEDDING_FN,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.add(
            ids=[c.metadata["chunk_id"] for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )

    print(f"Loaded {collection.count()} chunks into ChromaDB")
    print(f"Embedding model: {EMBEDDING_MODEL} (384 dim)")
    return collection

def get_collection() -> chromadb.Collection:
    client = get_client()
    return client.get_collection(name=COLLECTION_NAME, embedding_function=EMBEDDING_FN)

def _build_where(ctx: UserContext) -> dict:
    return {
        "$and": [
            {"tenant_id": ctx.tenant_id},
            {"classification": {"$in": ctx.allowed_classifications()}},
        ]
    }


def search(query: str, top_k: int = 5, user_ctx: UserContext | None = None) -> list[dict]:
    ctx = user_ctx or anonymous_context()
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=_build_where(ctx),
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    found = []
    for i in range(len(results["documents"][0])):
        meta = results["metadatas"][0][i]
        found.append({
            "text": results["documents"][0][i],
            "source": meta["source"],
            "distance": results["distances"][0][i],
            "tenant_id": meta.get("tenant_id"),
            "classification": meta.get("classification"),
        })
    return found

if __name__ == "__main__":
    results = search("How much does the Business plan cost?")
    for r in results:
        print(f"  [{r['source']}] (dist={r['distance']:.3f}) {r['text'][:120]}...")
