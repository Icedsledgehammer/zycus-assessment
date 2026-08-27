import json

from ollama import chat


class TAMSummarizer:
    """
    Generates only the interpretive portions of the TAM brief.

    Python remains the source of truth for:
    - account metadata
    - ticket metadata
    - risk classifications
    - severity
    - ticket IDs
    - evidence

    Qwen generates only:
    - account health summary
    - recommended actions
    """

    def __init__(self, model_name: str = "qwen3:4b"):
        self.model_name = model_name

    def _build_context(
        self,
        account: dict,
        tickets: list[dict],
        risks: list[dict],
    ) -> dict:
        """
        Send only information that Qwen actually needs.
        """

        account_context = {
            "company": account.get("company"),
            "plan_tier": account.get("plan_tier"),
            "arr_usd": account.get("arr_usd"),
            "health_status": account.get("health_status"),
            "usage_trend": account.get("usage_trend"),
            "open_tickets": account.get("open_tickets"),
            "p1_tickets_last_30d": account.get(
                "p1_tickets_last_30d"
            ),
            "renewal_date": account.get("renewal_date"),
            "last_qbr_date": account.get("last_qbr_date"),
            "escalation_notes": account.get(
                "escalation_notes",
                [],
            ),
            "nps_score": account.get("nps_score"),
            "last_login_days_ago": account.get(
                "last_login_days_ago"
            ),
        }

        ticket_context = []

        for ticket in tickets:
            ticket_context.append(
                {
                    "ticket_id": ticket.get("ticket_id"),
                    "product": ticket.get("product"),
                    "product_area": ticket.get(
                        "product_area"
                    ),
                    "category": ticket.get("category"),
                    "urgency": ticket.get("urgency"),
                    "status": ticket.get("status"),
                    "subject": ticket.get("subject"),
                    "body": ticket.get("body"),
                    "created_at": ticket.get("created_at"),
                }
            )

        risk_context = []

        for risk in risks:
            risk_context.append(
                {
                    "risk_type": risk.get("risk_type"),
                    "severity": risk.get("severity"),
                    "source": risk.get("source"),
                    "ticket_id": risk.get("ticket_id"),
                    "reason": risk.get("reason"),
                }
            )

        return {
            "account": account_context,
            "tickets": ticket_context,
            "verified_risks": risk_context,
        }

    def build_prompt(
        self,
        account: dict,
        tickets: list[dict],
        risks: list[dict],
    ) -> str:

        context = self._build_context(
            account=account,
            tickets=tickets,
            risks=risks,
        )

        context_json = json.dumps(
            context,
            indent=2,
            ensure_ascii=False,
        )

        return f"""
You are a Technical Account Manager briefing assistant.

Create ONLY the interpretive portions of an internal TAM brief.

Use ONLY the supplied information.

STRICT RULES:

1. Do not invent facts.
2. Do not invent dates, metrics, statuses, ticket IDs,
   products, product areas, or customer intentions.
3. Do not change any supplied account or ticket information.
4. Do not create new risks.
5. Do not assign severity.
6. Do not generate ticket IDs.
7. Do not generate evidence quotes.
8. Do not reproduce ticket evidence.
9. Do not claim a ticket is open, closed, resolved, or pending
   unless that exact status is supplied.
10. Do not infer a customer's intention unless explicitly stated.
11. Recommended actions must be grounded in the supplied
    account and risk information.
12. If information is unavailable, do not guess.
13. Keep the output concise and professional.

The Python application is the source of truth for all structured
metadata, risk classifications, severity, ticket IDs, and evidence.

Your responsibility is ONLY to produce:

1. A concise account health summary.
2. A short list of grounded recommended actions.

SUPPLIED DATA:

{context_json}

Return JSON ONLY.

Use EXACTLY this schema:

{{
  "account_health_summary": "Brief factual summary of the account health.",
  "recommended_actions": [
    "Grounded recommended action."
  ]
}}

Do not add any other fields.
"""

    def generate(
        self,
        account: dict,
        tickets: list[dict],
        risks: list[dict],
    ) -> str:

        prompt = self.build_prompt(
            account=account,
            tickets=tickets,
            risks=risks,
        )

        response = chat(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response.message.content
