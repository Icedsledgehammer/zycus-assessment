# Zycus Repository Analysis

## Design Note

This repository implements a multi-stage support automation pipeline
covering ticket triage, account-risk analysis, and evaluation. The
design deliberately keeps deterministic business logic separate from
LLM-generated interpretation. This reduces the amount of information
that an LLM is trusted to invent or modify.

## 1. Failure Modes

### 1.1 Invalid or unstructured LLM output

The LLM may return malformed JSON, incomplete fields, or additional
prose instead of the required schema. This can break downstream
processing and evaluation.

**Detection:** Validate every LLM response against the expected JSON
structure before using it. Record parsing failures as evaluation errors
rather than silently accepting malformed data.

**Mitigation:** Use strict output schemas, low-temperature generation,
response cleaning where appropriate, and bounded retries. If retries
still fail, fail the individual case cleanly and preserve the error in
the evaluation report.

### 1.2 Hallucinated or incorrectly grounded information

A support model could invent ticket metadata, knowledge-base
conclusions, account risks, or customer intentions. This is particularly
dangerous because a plausible-looking response can still be factually
wrong.

**Detection:** Compare generated fields against the source data and use
deterministic checks for objective requirements. The evaluation harness
also uses an independent LLM judge to assess grounding, factual
correctness, completeness, and usefulness.

**Mitigation:** Keep structured metadata, risk classifications,
severity, ticket IDs, and evidence under Python control. The LLM is
restricted to interpretation such as summaries and recommended actions.
Retrieved knowledge is also treated as evidence rather than as
permission to invent missing facts.

### 1.3 Stale or inconsistent source data

The account and ticket datasets can disagree, as demonstrated by the
deliberate company mismatch in the evaluation data. A production system
could otherwise present conflicting information as if it were reliable.

**Detection:** Perform source-data consistency checks before generating
the final brief and surface detected inconsistencies as data-quality
warnings.

**Mitigation:** Never silently reconcile conflicting source records.
Preserve the original values, flag the discrepancy, and require human
review when the inconsistency could affect a customer-facing decision.

## 2. Latency vs Quality

The main latency trade-off is using a local LLM for interpretation while
keeping deterministic processing around it. Local inference avoids
sending customer data to an external service, but generation can still
take considerably longer than ordinary Python processing.

For the evaluation harness, an additional Gemini LLM-as-a-Judge provides
a second quality signal. This increases evaluation time and introduces
an API dependency, but it gives the system a semantic assessment that
exact-match rules cannot provide.

If latency became a hard production constraint, I would reduce
generation length first, use smaller/faster models where quality remains
acceptable, and reserve the external judge for offline evaluation rather
than the production request path. Deterministic checks would remain in
the synchronous path because they are inexpensive and predictable.

## 3. Data Sensitivity

Ticket and account information may contain personally identifiable or
commercially sensitive information. The safest design is therefore to
minimize what leaves the local environment.

The production path should prefer local inference for customer data and
should not send raw account records or ticket bodies to an external API
unless that transfer is explicitly approved. Secrets such as API keys
must be stored in environment variables and excluded from version
control.

When an external LLM is used for evaluation, the evaluator should
receive only the minimum information required for judging the output. A
production implementation should additionally redact or tokenize names,
contact information, identifiers, and other sensitive fields before
external evaluation.

The deterministic Python layer also limits exposure by controlling which
fields are passed to the LLM.

## 4. Scaling

At 10x ticket volume, the first pressure point would be LLM inference
and retrieval rather than the basic Python business logic. Processing
every ticket serially would increase latency and make throughput
dependent on the slowest generation.

The first scaling step would be to separate ingestion, retrieval,
inference, and evaluation into independently scalable stages. Ticket
processing could be queued and executed concurrently, with bounded
worker pools to prevent GPU or API saturation. Retrieval indexes should
be built once and reused rather than recomputed for every request.

For production evaluation, LLM-as-a-Judge should remain an
asynchronous/offline quality gate. Running two LLM calls for every
customer request would unnecessarily increase latency and cost.

At higher volume, observability should track latency, queue depth, model
failures, JSON validation failures, retrieval quality, and judge
disagreement. These metrics would identify whether the bottleneck is
inference, retrieval, external API capacity, or downstream processing.

## Design Principle

The central design principle is to use the LLM where interpretation adds
value, while keeping facts and hard business rules deterministic. This
makes failures easier to detect, keeps sensitive information under
tighter control, and allows the evaluation harness to distinguish
objective correctness from semantic quality.
