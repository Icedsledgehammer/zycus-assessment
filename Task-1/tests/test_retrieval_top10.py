from pathlib import Path

from Retrieval.kb_reader import load_knowledge_base
from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase
from Retrieval.rag import RAGRetriever


project_root = Path(__file__).resolve().parents[2]
kb_root = project_root / "knowledge-base"

chunks = load_knowledge_base(kb_root)

embedder = EmbeddingModel()

embeddings = embedder.encode(
    [chunk.text for chunk in chunks]
)

database = VectorDatabase()

database.add(
    embeddings=embeddings,
    chunks=chunks,
)

retriever = RAGRetriever(
    embedder=embedder,
    vector_db=database,
)


query = (
    "Request: bulk archive entries in DataBridge Pro Data Ingestion\n"
    "Currently DataBridge Pro only allows individual archive entries "
    "in the Data Ingestion module. As our usage has scaled to 116 "
    "users we urgently need bulk operations."
)

results = retriever.retrieve(
    query=query,
    top_k=10,
)


print("\n--- TOP 10 RETRIEVAL RESULTS ---\n")

for index, result in enumerate(results, start=1):
    chunk = result["chunk"]

    print(f"Result {index}")
    print(f"Similarity: {result['score']:.4f}")
    print(f"Source: {chunk.source}")
    print(f"Text: {chunk.text[:200]}")
    print("-" * 60)
