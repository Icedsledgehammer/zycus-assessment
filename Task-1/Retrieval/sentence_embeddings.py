from sentence_transformers import SentenceTransformer
import torch
from pathlib import Path
from Retrieval.kb_reader import load_knowledge_base


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)

    def encode(self, texts: list[str]):
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[2]
    kb_root = project_root / "knowledge-base"

    chunks = load_knowledge_base(kb_root)

    print(f"Loaded {len(chunks)} KB chunks.")

    embedder = EmbeddingModel()

    texts = [chunk.text for chunk in chunks]

    embeddings = embedder.encode(texts)

    print(f"Embedding shape: {embeddings.shape}")
