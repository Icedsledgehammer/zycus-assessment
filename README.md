# Zycus Support Ticket Triage

This repository contains my submission for the US Delivery Internship technical task. Task 1 builds a support-ticket triage service around the supplied tickets, customer accounts, and product knowledge base.

The aim is practical: take a ticket, find the most relevant internal guidance, ask a local language model to classify the issue, and return a consistent result that a support team can review. The model is not allowed to treat the whole internet, or its own memory, as the source of product facts. The retrieved knowledge-base content is the grounding context.

## What Task 1 Includes

- A Markdown knowledge-base loader with metadata for source files and headings.
- Chunking based on horizontal rules, with individual Markdown table rows kept as separate searchable chunks.
- Sentence embeddings using `all-MiniLM-L6-v2`.
- An in-memory FAISS vector index using normalized embeddings and inner-product similarity.
- Retrieval-Augmented Generation (RAG) that returns the top five results scoring at least `0.60`.
- A local Ollama integration using the `qwen3:4b` model.
- A prompt that defines the allowed categories, product areas, urgency tiers, grounding rules, and exact JSON format.
- Validation of the model response before it is returned.
- Automatic escalation for P1 tickets and tickets with no sufficiently relevant knowledge-base result.
- A FastAPI service with health and triage endpoints.

## Repository Layout

```text
data/
  tickets.json              # Synthetic support tickets
  accounts.json             # Synthetic customer account information
knowledge-base/
  products/                 # Product documentation
  troubleshooting/          # Cross-product troubleshooting guides
  billing/                  # Billing and plan information
  onboarding/               # Onboarding guidance
Task-1/
  Retrieval/
    kb_reader.py            # Markdown parsing and chunk creation
    sentence_embeddings.py  # SentenceTransformer wrapper
    vector_database.py      # FAISS index and similarity search
    rag.py                  # Query embedding and score filtering
  LLM/
    model.py                # Ollama chat wrapper
    prompts.py              # Triage prompt construction
  triage.py                 # End-to-end triage orchestration
  api.py                    # FastAPI application
  tests/                    # Retrieval, RAG, LLM, and triage checks
DATA_SCHEMA.md              # Dataset fields and enum definitions
requirements.txt            # Python dependencies
```

## How the Pipeline Works

When `TicketTriager` starts, it receives all knowledge-base chunks, encodes their text, and adds those embeddings to a FAISS `IndexFlatIP` index. The index and its chunks stay in memory for the lifetime of the process.

For each ticket, the subject and body are combined into one query. The query is embedded with the same model used for the knowledge base. FAISS ranks the chunks by similarity, and the RAG layer keeps only results above the configured `0.60` threshold. The API currently asks for five results; the retrieval example in `test_retrieval_top10.py` demonstrates that the same component can return ten.

Each result carries its similarity score, source path, heading metadata, chunk type, and text. Text chunks preserve normal prose, while table rows are isolated so that error-code and reference-table lookups do not bring an entire document into the prompt.

The selected results are inserted into a detailed prompt alongside the ticket. The prompt asks the local model to identify the product area, choose one allowed issue category, set an urgency tier, decide whether the specific issue is covered by the retrieved documentation, recommend a responder team, and draft a first response.

The model must return one JSON object. The application parses that response and checks that all required fields exist, the category and urgency are from the allowed lists, and the knowledge-base match flag is a real Boolean. Invalid JSON or invalid values become a clear `422` error when called through the API.

After validation, the application applies the human-review rules. A P1 result is always escalated. A ticket with no retrieved result above the similarity threshold is also escalated because there is not enough grounded information to answer it confidently. Escalated results include the ticket's existing assigned agent; non-escalated results leave that field empty.

## Output

The triage response contains:

```json
{
  "product_area": "Connectors",
  "issue_category": "Integration",
  "urgency_tier": "P2",
  "reasoning": "...",
  "matches_known_knowledge_base_issue": true,
  "relevant_knowledge_base_document": "products/databridge-pro.md",
  "recommended_responder_team": "Integrations Support",
  "draft_first_response_message": "...",
  "escalation_required": false,
  "escalation_reason": null,
  "assigned_agent": null
}
```

The first eight fields are produced and checked against the model contract. The last three fields are added by the application after that check.

## Setup

Use Python 3.10 or newer, create a virtual environment, and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install and start [Ollama](https://ollama.com), then download the configured model:

```powershell
ollama pull qwen3:4b
```

Ollama must be running before an LLM-backed triage request is made. The embedding model is downloaded by `sentence-transformers` on its first use. CUDA is used automatically when PyTorch detects a CUDA device; otherwise embeddings run on the CPU.

## Running Task 1

From the `Task-1` directory, run the API with Uvicorn:

```powershell
cd Task-1
uvicorn api:app --reload
```

The service is then available at `http://127.0.0.1:8000`. FastAPI's interactive documentation is available at `/docs`.

### Health check

```powershell
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Triage a ticket

The `/triage` endpoint accepts a ticket object in the request body. It can receive a record directly from `data/tickets.json` or another object with the same useful fields:

```powershell
curl -X POST http://127.0.0.1:8000/triage `
  -H "Content-Type: application/json" `
  --data-binary '@ticket.json'
```

The application loads the knowledge base when `api.py` starts, so the initial startup can take longer while the embedding model is loaded and the index is built.

## Testing and Examples

The files in `Task-1/tests` are executable checks and demonstrations for the main pieces of the system:

- `test_embedding_similarity.py` compares direct embedding similarity for a sample authentication query.
- `test_vector_database.py` exercises the FAISS-backed search path.
- `test_rag.py` prints filtered retrieval results and their metadata.
- `test_retrieval_top10.py` demonstrates top-ten retrieval for a DataBridge Pro request.
- `test_llm.py` and `test_llm_triage.py` exercise the local model and prompt path.
- `test_triage.py` runs the complete pipeline against a supplied ticket.

Most of these files are script-style checks with a `__main__` entry point, so run an individual check from `Task-1` with:

```powershell
python tests/test_rag.py
```

The retrieval-only checks do not require Ollama. The LLM and end-to-end checks do.

## Design Decisions and Limitations

The knowledge base is loaded from Markdown instead of being copied into code, which keeps the source of product guidance visible and easy to update. Heading metadata is retained for debugging and inspection. Normalized embeddings make inner-product scores behave like cosine similarity, keeping the retrieval calculation simple.

The local model keeps the project self-contained and avoids sending ticket data to a hosted model. The trade-off is that Ollama must be installed, the model must be present, and response speed depends on the local machine.

The current vector index is rebuilt at application startup and is not persisted. There is no authentication, database-backed ticket storage, request schema model, retry logic for Ollama, or conversation history. Escalation currently uses only the model's urgency, retrieval availability, and the ticket's existing assigned agent. These are sensible next steps for a production version, but are outside the scope of Task 1.

## Data Notes

The data is synthetic. Tickets link to accounts through `account_id`, but the supplied schema notes that some account references may not have a matching account record. `DATA_SCHEMA.md` documents the ticket and account fields, enum values, and the recommended way to join the datasets.

## Assessment Progress

Task 1 is implemented: knowledge-base retrieval, embeddings, vector search, RAG context construction, local LLM triage, structured output validation, escalation handling, and the REST API are all present under `Task-1`.
