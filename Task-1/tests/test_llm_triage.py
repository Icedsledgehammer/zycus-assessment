import json
from pathlib import Path

from Retrieval.kb_reader import load_knowledge_base
from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase
from Retrieval.rag import RAGRetriever

from LLM.model import LLM
from LLM.prompts import build_triage_prompt


def load_ticket(ticket_id: str):
    project_root = Path(__file__).resolve().parents[2]
    tickets_path = project_root / "data" / "tickets.json"

    with tickets_path.open("r", encoding="utf-8") as file:
        tickets = json.load(file)

    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket

    raise ValueError(f"Ticket not found: {ticket_id}")


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

    ticket = load_ticket("TKT-10000")

    query = f"{ticket['subject']}\n{ticket['body']}"

    retrieved_results = rag.retrieve(
        query=query,
        top_k=5,
    )

    prompt = build_triage_prompt(
        ticket=ticket,
        retrieved_results=retrieved_results,
    )

    llm = LLM()

    response = llm.generate(prompt)

    print("\n--- LLM TRIAGE OUTPUT ---\n")
    print(response)
