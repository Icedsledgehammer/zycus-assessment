import json
from pathlib import Path

from Retrieval.kb_reader import load_knowledge_base
from triage import TicketTriager


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

    triager = TicketTriager(chunks)

    ticket = load_ticket("TKT-10000")

    # print("\nTicket:")  # Just for debugging purposes, uncomment if needed
    # print(ticket)       # Just checking whether the ticket is loaded correctly, uncomment if needed

    print("\nRetrieved KB:")
    retrieved_results = triager.rag.retrieve(
        f"{ticket['subject']}\n{ticket['body']}",
        top_k=5,
    )

    for result in retrieved_results:
        print(result["score"])
        print(result["chunk"].text)

    result = triager.triage_ticket(ticket)

    print("\n--- FINAL TRIAGE RESULT ---\n")
    print(json.dumps(result, indent=2))
