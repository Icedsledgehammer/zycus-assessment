from pathlib import Path

from fastapi import FastAPI, HTTPException

from Retrieval.kb_reader import load_knowledge_base
from triage import TicketTriager


app = FastAPI(
    title="Zycus Support Ticket Triage",
    version="1.0.0",
)


project_root = Path(__file__).resolve().parents[1]
kb_root = project_root / "knowledge-base"

chunks = load_knowledge_base(kb_root)

triager = TicketTriager(chunks)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/triage")
def triage_ticket(ticket: dict):
    try:
        return triager.triage_ticket(ticket)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Ticket triage failed.",
        ) from error
