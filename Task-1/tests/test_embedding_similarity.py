from pathlib import Path

import numpy as np

from Retrieval.kb_reader import load_knowledge_base
from Retrieval.sentence_embeddings import EmbeddingModel


def find_similar_chunks(
    query: str,
    chunks,
    embeddings: np.ndarray,
    embedder: EmbeddingModel,
    top_k: int = 5,
):
    query_embedding = embedder.encode([query])[0]

    scores = embeddings @ query_embedding

    top_indices = np.argsort(scores)[-top_k:][::-1]

    return [
        (float(scores[index]), chunks[index])
        for index in top_indices
    ]

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]
    kb_root = project_root / "knowledge-base"

    chunks = load_knowledge_base(kb_root)

    embedder = EmbeddingModel()

    texts = [chunk.text for chunk in chunks]
    embeddings = embedder.encode(texts)

    query = "Users are unable to authenticate using SAML"

    results = find_similar_chunks(
        query=query,
        chunks=chunks,
        embeddings=embeddings,
        embedder=embedder,
        top_k=5,
    )

    print(f"\nQuery: {query}\n")

    for rank, (score, chunk) in enumerate(results, start=1):
        print(f"--- Result {rank} ---")
        print(f"Similarity: {score:.4f}")
        print(f"Source: {chunk.source}")
        print(f"Headings: {chunk.headings}")
        print(f"Type: {chunk.chunk_type}")
        print(f"Text: {chunk.text[:300]}")
        print()
