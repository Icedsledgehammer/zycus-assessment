# Zycus Support Operations Assessment

This repository contains my submission for the US Delivery Internship technical task. It uses the supplied synthetic support-ticket data, customer-account data, and product knowledge base to build two related support operations tools.

- **Task 1** is an AI-assisted support ticket triage service.
- **Task 2** is a TAM account health summariser that turns account data and recent support activity into an internal account brief.

Both tasks expose FastAPI endpoints and use a local Ollama model where natural-language interpretation is useful. The parts that need to be exact, traceable, and reproducible are kept in Python rather than delegated to the model.

## Project Data

The `data` folder contains two JSON datasets:

- `tickets.json` contains ticket IDs, account IDs, companies, subjects, descriptions, products, product areas, categories, urgency, status, dates, and other support metadata.
- `accounts.json` contains account health, plan tier, ARR, licensed and active seats, products, usage trend, open-ticket counts, P1 history, renewal information, NPS, login recency, escalation notes, and customer details.

The `knowledge-base` folder contains Markdown documentation grouped into products, troubleshooting, billing, and onboarding. `DATA_SCHEMA.md` documents the fields, allowed values, relationships, and data-quality assumptions in more detail.

The data is synthetic. Tickets are related to accounts through `account_id`, but the supplied data can contain incomplete or inconsistent relationships. The implementation keeps those issues visible instead of silently changing the source data.

## Repository Layout

```text
data/
  tickets.json                    # Synthetic support tickets
  accounts.json                   # Synthetic account records
knowledge-base/
  products/                       # Product documentation
  troubleshooting/                # Troubleshooting guides
  billing/                        # Billing and plan information
  onboarding/                     # Onboarding information
Task-1/
  Retrieval/
    __init__.py
    kb_reader.py                  # Markdown parsing and chunk creation
    sentence_embeddings.py        # SentenceTransformer wrapper
    vector_database.py             # FAISS index and similarity search
    rag.py                         # Retrieval and score filtering
  LLM/
    model.py                       # Ollama chat wrapper
    prompts.py                    # Triage prompt construction
  triage.py                       # End-to-end ticket triage
  api.py                          # Task 1 FastAPI application
  tests/                          # Retrieval, RAG, LLM, and triage checks
Task-2/
  data_loader.py                  # Account and ticket loading
  risk_detection.py               # Deterministic risk detection
  summarizer.py                   # LLM summary and action generation
  brief_builder.py                # Final response assembly
  api.py                          # Task 2 FastAPI application
  tests/                          # Task 2 API, risk, and summariser tests
DATA_SCHEMA.md                    # Dataset schema reference
requirements.txt                  # Python dependencies
README.md                         # Project documentation
```

## Task 1: AI Support Ticket Triage

### Purpose

Task 1 accepts a support ticket and produces a structured triage result. It uses semantic search to find relevant internal documentation, then gives that context to a local language model so the model can classify the ticket and draft an initial response.

The knowledge base is treated as the authoritative source for product-specific information. The prompt explicitly tells the model not to invent product capabilities, configuration values, error codes, policies, dates, limits, or troubleshooting steps.

### Knowledge-base processing

`Task-1/Retrieval/kb_reader.py` reads every Markdown file below `knowledge-base` recursively and sorts the files for repeatable loading. Each file is split at horizontal-rule lines (`---`), following the chunking recommendation in the supplied schema.

The parser also tracks Markdown heading hierarchy. A chunk retains its source path and heading metadata, such as the product and section it came from. Regular prose is kept as a text chunk. Markdown table rows are separated into their own chunks, while the table header and separator row are skipped. This makes small, structured references such as error-code tables easier to retrieve without including a whole document.

Each chunk is represented by `KBChunk` with:

- `text`: the searchable content
- `source`: the path relative to `knowledge-base`
- `headings`: the active heading hierarchy
- `chunk_type`: either normal text or a table row

### Embeddings and search

`sentence_embeddings.py` wraps `SentenceTransformer` and uses the `all-MiniLM-L6-v2` model by default. The model selects CUDA when PyTorch reports that CUDA is available and otherwise uses the CPU. Embeddings are normalized before they are stored or searched.

`vector_database.py` stores the embeddings in an in-memory FAISS `IndexFlatIP` index. Because the vectors are normalized, inner-product scores act as cosine-similarity scores. The class checks that the number of embeddings matches the number of chunks and that the embedding array is two-dimensional before creating the index.

`rag.py` embeds the incoming query, searches the vector index, and filters out results below a similarity score of `0.60`. The normal triage path requests the top five results. The retrieval example also demonstrates that the same component can request ten results.

### Triage and model output

`triage.py` creates the embedding model, builds the vector database, creates the RAG retriever, and initializes the local LLM. For every ticket, it combines the subject and body into a query, retrieves relevant knowledge, builds the prompt, and calls the model.

The prompt requires exactly one JSON object with these fields:

- `product_area`
- `issue_category`
- `urgency_tier`
- `reasoning`
- `matches_known_knowledge_base_issue`
- `relevant_knowledge_base_document`
- `recommended_responder_team`
- `draft_first_response_message`

The allowed issue categories are `Data Loss`, `Feature Request`, `Performance`, `How-To`, `Onboarding`, `Bug`, `Billing`, and `Integration`. The allowed urgency values are `P1`, `P2`, `P3`, and `P4`. The prompt also distinguishes a product from its product area and asks the model to judge urgency from actual technical or business impact rather than from words such as "urgent" alone.

The response is parsed with `json.loads`. Before it is used, the application checks that it is an object, contains every required field, uses an allowed category and urgency, and represents `matches_known_knowledge_base_issue` as a Boolean. Invalid model output raises a `ValueError`, which the API exposes as HTTP `422`.

### Escalation

Escalation is applied after model validation:

- A `P1` result always requires human intervention.
- A ticket with no result above the retrieval threshold is escalated because there is not enough grounded knowledge to answer it safely.
- An escalated result includes the ticket's existing `assigned_agent` value.
- A result that does not meet either condition has `escalation_required` set to `false`, with no escalation reason or assigned agent added.

This means the model supplies the classification and explanation, but the final escalation rule is controlled by the application.

### Task 1 API

`Task-1/api.py` exposes:

- `GET /health` returns `{"status": "ok"}`.
- `POST /triage` accepts a ticket object and returns the structured triage result.

The knowledge base and vector index are built when the API module starts. The first startup can therefore take longer while the embedding model is loaded and the documents are encoded. The vector index is currently held in memory and rebuilt on every process start.

## Task 2: TAM Account Health Summariser

### Purpose

Task 2 creates an internal brief for a Technical Account Manager. Given an account ID, it combines the account's current health information with recent support activity, identifies risks, and returns a concise summary with recommended actions.

The important design choice is that Python remains responsible for structured and evidence-based information. The LLM is used only for the interpretive parts: the account-health summary and recommended actions.

### Loading the account context

`Task-2/data_loader.py` loads both JSON files when `AccountDataLoader` is created. It finds the requested account by `account_id` and raises an error when the account does not exist.

Recent tickets are selected for the requested account over a 90-day period by default. Since the dataset is historical rather than continuously updated, the implementation uses the latest ticket timestamp for that account as the reference date, then includes tickets from that date back to the 90-day cutoff. The returned tickets are sorted by `created_at`.

The loader also checks the company recorded on each ticket against the company recorded on the account. A mismatch is returned as a data-quality warning containing the ticket ID, account ID, account company, and ticket company.

### Deterministic risk detection

`Task-2/risk_detection.py` does not ask the model to decide whether a risk exists. It derives risks directly from account fields, ticket metadata, and ticket text.

Account-level checks include:

- `Churn` when the account health is marked `Churning`.
- `Account Health` when the account is marked `At Risk`.
- `Usage Decline` when usage is declining.
- `Usage Inactivity` when usage is inactive.
- `Critical Incidents` when the account has one or more P1 tickets in the last 30 days.
- A churn signal from escalation notes containing terms such as competitor, switching, cancellation, non-renewal, or churn.

Ticket-level checks include:

- `Critical Incident` for a P1 ticket.
- `High Priority Issue` for a P2 ticket.
- `Churn Signal` when the subject or body contains churn-related language.
- `Escalation Signal` when it contains language such as escalation, manager, executive, immediately, urgent, ASAP, or critical.
- `Operational Impact` when it describes slow performance, timeouts, unavailability, outages, blocked work, failures, data loss, business impact, or affected users.

The detector uses regular expressions with case-insensitive searchable text. It assigns severity according to fixed rules, keeps the source as either `account` or `ticket`, and includes the ticket ID when applicable. Operational impact is marked high when at least two matching indicators are found; otherwise it is medium. Duplicate risks are removed using their type, ticket ID, evidence, and reason.

Evidence is copied from the original ticket. For ticket-level matches, the detector returns the matching line or sentence as an `evidence_quote`; it does not ask the LLM to invent or rewrite evidence.

### LLM summarisation

`Task-2/summarizer.py` sends Qwen a restricted context containing selected account fields, recent ticket fields, and verified risks. The prompt explicitly tells the model not to invent facts, dates, metrics, statuses, ticket IDs, products, customer intentions, risks, severity, or evidence quotes.

The model returns only:

```json
{
  "account_health_summary": "Brief factual summary of the account health.",
  "recommended_actions": [
    "Grounded recommended action."
  ]
}
```

The model does not produce the complete brief. This limits the chance that generated prose changes the underlying account or support data.

### Building the final brief

`Task-2/brief_builder.py` parses the model JSON and assembles the response deterministically. It includes:

- `account_health`: the source health status and usage trend, plus the generated summary.
- `recent_support_activity`: ticket ID, product, product area, category, urgency, status, subject, and evidence quotes.
- `risks`: risk type, severity, source, reason, ticket ID where relevant, and evidence where available.
- `recommended_actions`: the model's grounded action list.

The API adds `data_quality_warnings` separately so users can distinguish account risks from inconsistencies in the source data.

### Task 2 API

`Task-2/api.py` exposes:

- `GET /health` returns the service status and the service name, `TAM Account Health Summariser`.
- `GET /accounts/{account_id}/brief` returns the account brief for the requested account.
- An unknown account returns HTTP `404` with an explanatory detail message.

For example, `GET /accounts/ACC-3336/brief` returns the account's `At Risk` status, inactive usage trend, recent support activity, detected risks, recommended actions, and any data-quality warnings found in the 90-day context.

## Setup

Use Python 3.10 or newer. From the repository root, create and activate a virtual environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Both tasks use the local Ollama model `qwen3:4b`. Install Ollama, start it, and pull the model:

```powershell
ollama pull qwen3:4b
```

The embedding model used by Task 1 is downloaded by `sentence-transformers` on first use. Task 2 also needs Ollama when generating a brief because its summary and recommended actions come from Qwen.

## Running the APIs

Run each task from its own directory so its local imports resolve correctly.

### Task 1

```powershell
cd Task-1
uvicorn api:app --reload
```

The Task 1 service runs at `http://127.0.0.1:8000`. Open `/docs` for the interactive FastAPI documentation.

Example health request:

```powershell
curl http://127.0.0.1:8000/health
```

Example triage request using a JSON file containing one ticket:

```powershell
curl -X POST http://127.0.0.1:8000/triage `
  -H "Content-Type: application/json" `
  --data-binary '@ticket.json'
```

### Task 2

Stop the Task 1 server first, or use another port, then run:

```powershell
cd Task-2
uvicorn api:app --reload
```

The Task 2 service also defaults to `http://127.0.0.1:8000`. Example requests:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/accounts/ACC-3336/brief
```

When both services need to run at the same time, start the second one on another port, for example:

```powershell
uvicorn api:app --reload --port 8001
```

## Testing

Task 1 contains checks for the knowledge-base reader, embedding similarity, FAISS vector search, RAG filtering, LLM prompting, and end-to-end triage. Its scripts can be run from the `Task-1` directory, for example:

```powershell
cd Task-1
python tests/test_rag.py
python tests/test_triage.py
```

The retrieval-only examples do not need Ollama. The LLM and full triage examples do.

Task 2 contains focused checks for its API, deterministic risk rules, and summariser:

```powershell
cd Task-2
python -m tests.test_api
python -m tests.test_risk_detection
python -m tests.test_summarizer
```

The API test covers the health response, the `ACC-3336` brief structure and expected risk/data-quality behavior, and the `404` response for `ACC-9999`. The summariser test requires Ollama because it exercises the local model.

## Current Limitations

- The FAISS index is rebuilt in memory whenever Task 1 starts; it is not persisted.
- Neither API has authentication or database-backed storage.
- Request bodies are currently accepted as dictionaries rather than strict Pydantic request models.
- There is no retry or timeout policy around Ollama calls.
- The local model and embedding model must be installed separately.
- Task 2 uses the latest ticket date as its dataset reference point, which is useful for the supplied historical data but is different from using the machine's current date.
- Task 2 reports company mismatches, but it does not modify or discard the affected tickets.
- The current escalation logic is intentionally limited to the rules described above.

## Assessment Status

Task 1 includes knowledge-base processing, semantic retrieval, RAG context construction, local LLM triage, structured output validation, escalation handling, and a REST API.

Task 2 includes account-context loading, 90-day support activity selection, deterministic risk detection with source evidence, local LLM summarisation, data-quality warnings, final brief assembly, and a REST API.
