import json


def build_final_brief(
    account: dict,
    tickets: list[dict],
    risks: list[dict],
    llm_output: str,
) -> dict:

    llm_data = llm_output

    recent_support_activity = []

    for ticket in tickets:

        ticket_id = ticket.get("ticket_id")

        ticket_risks = [
            risk
            for risk in risks
            if risk.get("source") == "ticket"
            and risk.get("ticket_id") == ticket_id
        ]

        evidence_quotes = []

        for risk in ticket_risks:

            evidence = risk.get("evidence_quote")

            if evidence and evidence not in evidence_quotes:
                evidence_quotes.append(evidence)

        recent_support_activity.append(
            {
                "ticket_id": ticket_id,
                "product": ticket.get("product"),
                "product_area": ticket.get("product_area"),
                "category": ticket.get("category"),
                "urgency": ticket.get("urgency"),
                "status": ticket.get("status"),
                "subject": ticket.get("subject"),
                "evidence_quotes": evidence_quotes,
            }
        )

    risk_output = []

    for risk in risks:

        risk_entry = {
            "risk_type": risk.get("risk_type"),
            "severity": risk.get("severity"),
            "source": risk.get("source"),
            "reason": risk.get("reason"),
        }

        if risk.get("ticket_id"):
            risk_entry["ticket_id"] = risk.get("ticket_id")

        if risk.get("evidence_quote"):
            risk_entry["evidence_quote"] = risk.get(
                "evidence_quote"
            )

        risk_output.append(risk_entry)

    return {
        "account_health": {
            "status": account.get("health_status"),
            "usage_trend": account.get("usage_trend"),
            "summary": llm_data.get(
                "account_health_summary",
                "",
            ),
        },
        "recent_support_activity": recent_support_activity,
        "risks": risk_output,
        "recommended_actions": llm_data.get(
            "recommended_actions",
            [],
        ),
    }
