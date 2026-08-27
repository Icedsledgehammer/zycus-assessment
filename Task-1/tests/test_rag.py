from pathlib import Path

from Retrieval.kb_reader import load_knowledge_base
from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase
from Retrieval.rag import RAGRetriever


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    kb_root = project_root / "knowledge-base"

    chunks = load_knowledge_base(kb_root)

    embedder = EmbeddingModel()

    texts = [chunk.text for chunk in chunks]
    embeddings = embedder.encode(texts)

    vector_db = VectorDatabase()

    vector_db.add(
        embeddings=embeddings,
        chunks=chunks,
    )

    rag = RAGRetriever(
        embedder=embedder,
        vector_db=vector_db,
    )

    query = "Users are unable to authenticate using SAML"

    results = rag.retrieve(
        query=query,
        top_k=5,
    )

    print(f"\nQuery: {query}\n")

    for rank, result in enumerate(results, start=1):
        chunk = result["chunk"]

        print(f"--- Result {rank} ---")
        print(f"Similarity: {result['score']:.4f}")
        print(f"Source: {chunk.source}")
        print(f"Headings: {chunk.headings}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Text: {chunk.text[:300]}")
        print()
