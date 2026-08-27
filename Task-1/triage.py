import json

from Retrieval.sentence_embeddings import EmbeddingModel
from Retrieval.vector_database import VectorDatabase
from Retrieval.rag import RAGRetriever

from LLM.model import LLM
from LLM.prompts import build_triage_prompt


ALLOWED_CATEGORIES = {
    "Data Loss",
    "Feature Request",
    "Performance",
    "How-To",
    "Onboarding",
    "Bug",
    "Billing",
    "Integration",
}

ALLOWED_URGENCY = {
    "P1",
    "P2",
    "P3",
    "P4",
}

REQUIRED_FIELDS = {
    "product_area",
    "issue_category",
    "urgency_tier",
    "reasoning",
    "matches_known_knowledge_base_issue",
    "relevant_knowledge_base_document",
    "recommended_responder_team",
    "draft_first_response_message",
}


class TicketTriager:
    def __init__(self, kb_chunks):
        self.embedder = EmbeddingModel()

        embeddings = self.embedder.encode(
            [chunk.text for chunk in kb_chunks]
        )

        self.vector_db = VectorDatabase()

        self.vector_db.add(
            embeddings=embeddings,
            chunks=kb_chunks,
        )

        self.rag = RAGRetriever(
            embedder=self.embedder,
            vector_db=self.vector_db,
        )

        self.llm = LLM()

    def triage_ticket(self, ticket: dict) -> dict:
        query = (
            f"{ticket.get('subject', '')}\n"
            f"{ticket.get('body', '')}"
        )

        retrieved_results = self.rag.retrieve(
            query=query,
            top_k=5,
        )

        prompt = build_triage_prompt(
            ticket=ticket,
            retrieved_results=retrieved_results,
        )

        response = self.llm.generate(prompt)

        result = self._parse_response(response)

        self._validate_result(result)

        result = self._apply_escalation(
            result,
            ticket,
            retrieved_results,
        )

        return result

    def _parse_response(self, response: str) -> dict:
        try:
            result = json.loads(response)
        except json.JSONDecodeError as error:
            raise ValueError(
                "LLM returned invalid JSON."
            ) from error

        if not isinstance(result, dict):
            raise ValueError("LLM response must be a JSON object.")

        return result

    def _validate_result(self, result: dict):
        missing_fields = REQUIRED_FIELDS - result.keys()

        if missing_fields:
            raise ValueError(
                f"LLM response is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if result["issue_category"] not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid issue category: "
                f"{result['issue_category']}"
            )

        if result["urgency_tier"] not in ALLOWED_URGENCY:
            raise ValueError(
                f"Invalid urgency tier: "
                f"{result['urgency_tier']}"
            )

        if not isinstance(
            result["matches_known_knowledge_base_issue"],
            bool,
        ):
            raise ValueError("matches_known_knowledge_base_issue must be a boolean.")

    def _apply_escalation(
        self,
        result: dict,
        ticket: dict,
        retrieved_results: list,
    ) -> dict:

        escalation_required = False
        escalation_reason = None

        if result["urgency_tier"] == "P1":
            escalation_required = True
            escalation_reason = "P1 ticket requires human intervention."

        elif not retrieved_results:
            escalation_required = True
            escalation_reason = (
                "No sufficiently relevant knowledge-base information "
                "was retrieved."
            )

        if escalation_required:
            result["escalation_required"] = True
            result["escalation_reason"] = escalation_reason
            result["assigned_agent"] = ticket.get("assigned_agent")

        else:
            result["escalation_required"] = False
            result["escalation_reason"] = None
            result["assigned_agent"] = None

        return result
