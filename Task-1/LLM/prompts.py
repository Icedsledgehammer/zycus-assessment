def build_triage_prompt(ticket: dict, retrieved_results: list) -> str:
    subject = ticket.get("subject", "")
    body = ticket.get("body", "")

    context_parts = []

    for index, result in enumerate(retrieved_results, start=1):
        chunk = result["chunk"]

        context_parts.append(
            f"""
[KB Result {index}]
Similarity: {result["score"]:.4f}
Source: {chunk.source}
Type: {chunk.chunk_type}

{chunk.text}
"""
        )

    knowledge_context = "\n".join(context_parts)

    prompt = f"""
You are an AI support ticket triage assistant.

Analyze the support ticket using the retrieved knowledge-base
context provided below.

The knowledge base should be treated as the authoritative
source for product-specific information.

Do not invent product-specific troubleshooting steps.
If the retrieved knowledge is insufficient to confidently
address the issue, indicate that escalation is appropriate.

TICKET

Subject:
{subject}

Body:
{body}

RETRIEVED KNOWLEDGE

{knowledge_context}

Determine the following:

1. Product area
2. Issue category
3. Urgency tier (P1, P2, P3, or P4)
4. Reasoning for the classification
5. Whether the ticket matches a known knowledge-base issue
6. Relevant knowledge-base document
7. Recommended responder team
8. Draft first-response message

Return the result as JSON only.
"""

    return prompt
