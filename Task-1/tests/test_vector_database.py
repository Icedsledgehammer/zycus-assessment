from pathlib import Path

from Retrieval.kb_reader import load_knowledge_base
from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase

if __name__ == "__main__":
    # Load the knowledge base

    project_root = Path(__file__).resolve().parents[2]
    kb_root = project_root / "knowledge-base"

    # print(f"Project root: {project_root}")
    # print(f"KB path: {kb_root}")               # #Testing whether the paths are correct or not
    # print(f"KB exists: {kb_root.exists()}")

    chunks = load_knowledge_base(kb_root)

    embedder = EmbeddingModel()
    texts = [chunk.text for chunk in chunks]

    embeddings = embedder.encode(texts)

    # print(f"Embedding type: {type(embeddings)}")       # Returns the type of embeddings, which is a numpy array. Again, this is only a sanity check
    # print(f"Embedding shape: {embeddings.shape}")      # Returns the shape of the embeddings, which is a tuple. Sanity check thats it

    database = VectorDatabase()

    database.add(
        embeddings=embeddings,
        chunks=chunks,
    )

    query = "Users are unable to authenticate using SAML"

    query_embedding = embedder.encode([query])

    results = database.search(
        query_embedding=query_embedding,
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
