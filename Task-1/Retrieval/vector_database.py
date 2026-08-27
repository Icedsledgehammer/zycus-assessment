import faiss
import numpy as np


class VectorDatabase:
    def __init__(self):
        self.index = None
        self.chunks = []

    def add(self, embeddings: np.ndarray, chunks):
        if len(embeddings) != len(chunks):
            raise ValueError("Embeddings and chunks must have the same length.")

        dimension = embeddings.shape[1]

        if embeddings.ndim != 2:
            raise ValueError(
                "Embeddings must be a 2D array."
            )

        if embeddings.shape[0] != len(chunks):
            raise ValueError(
                "Number of embeddings must match number of chunks."
            )

        self.index = faiss.IndexFlatIP(dimension)

        self.index.add(embeddings.astype(np.float32))

        self.chunks = list(chunks)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ):
        if self.index is None:
            raise RuntimeError("Vector Database has not been initialized")

        query_embedding = np.asarray(query_embedding, dtype=np.float32)

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        scores, indices = self.index.search(query_embedding, top_k)

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index == -1:
                continue

            results.append(
                {
                    "score": float(score),
                    "chunk": self.chunks[index],
                }
            )

        return results
