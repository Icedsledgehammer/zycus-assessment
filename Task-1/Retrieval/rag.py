from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase

class RAGRetriever:
    def __init__(
            self,
            embedder: EmbeddingModel,
            vector_db: VectorDatabase,
    ):
        self.embedder = embedder
        self.vector_db = vector_db

    def retrieve(
            self,
            query: str,
            top_k: int = 5
    ):
        query_embedding = self.embedder.encode([query])

        return self.vector_db.search(query_embedding, top_k=top_k)
