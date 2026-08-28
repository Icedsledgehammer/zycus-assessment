def _is_valid_value(value, expected):
    """
    Compare a value against an expected value.

    Supports:
    - exact values
    - lists
    - dictionaries
    - boolean values
    """

    if isinstance(expected, list):
        return value in expected

    if isinstance(expected, dict):
        if not isinstance(value, dict):
            return False

        return all(
            value.get(key) == expected_value
            for key, expected_value in expected.items()
        )

    return value == expected


def _contains_text(value, expected_text):
    if not isinstance(value, str):
        return False

    return expected_text.lower() in value.lower()


# ============================================================
# TASK 1 EVALUATION
# ============================================================

def evaluate_task1(output: dict, case: dict) -> dict:
    """
    Evaluate a Task 1 ticket-triage output.

    Evaluation is deterministic and based on explicit
    acceptance criteria defined in the evaluation case.
    """

    expected = case.get("expected", {})

    checks = {}

    # --------------------------------------------------------
    # Product area
    # --------------------------------------------------------

    if "product_area" in expected:
        checks["product_area"] = (
            output.get("product_area")
            == expected["product_area"]
        )

    # --------------------------------------------------------
    # Issue category
    # --------------------------------------------------------

    if "issue_category" in expected:
        checks["issue_category"] = (
            output.get("issue_category")
            == expected["issue_category"]
        )

    # --------------------------------------------------------
    # Urgency
    # --------------------------------------------------------

    if "urgency_tier" in expected:
        checks["urgency_tier"] = (
            output.get("urgency_tier")
            == expected["urgency_tier"]
        )

    # --------------------------------------------------------
    # Knowledge-base match
    # --------------------------------------------------------

    if "matches_known_knowledge_base_issue" in expected:
        checks["kb_match"] = (
            output.get("matches_known_knowledge_base_issue")
            == expected["matches_known_knowledge_base_issue"]
        )

    # --------------------------------------------------------
    # Relevant KB document
    # --------------------------------------------------------

    if "relevant_knowledge_base_document" in expected:
        checks["kb_document"] = (
            output.get("relevant_knowledge_base_document")
            == expected["relevant_knowledge_base_document"]
        )

    # --------------------------------------------------------
    # Responder team
    # --------------------------------------------------------

    if "recommended_responder_team" in expected:
        expected_team = expected["recommended_responder_team"]
        actual_team = output.get("recommended_responder_team")

        if expected_team is None:
            checks["responder_team"] = actual_team is None
        else:
            checks["responder_team"] = (
                actual_team is not None
                and expected_team.lower() in actual_team.lower()
            )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_fields = [
        "product_area",
        "issue_category",
        "urgency_tier",
        "reasoning",
        "matches_known_knowledge_base_issue",
        "recommended_responder_team",
        "draft_first_response_message",
    ]

    checks["valid_structure"] = all(
        field in output
        for field in required_fields
    )

    return {
        "case_id": case["case_id"],
        "task": "Task 1",
        "checks": checks,
    }


# ============================================================
# TASK 2 EVALUATION
# ============================================================

def evaluate_task2(output: dict, case: dict) -> dict:
    """
    Evaluate a Task 2 TAM account-health brief.

    Deterministic checks are performed against account health,
    support activity, risks, evidence and recommendations.
    """

    expected = case.get("expected", {})

    checks = {}

    # --------------------------------------------------------
    # Account health
    # --------------------------------------------------------

    expected_health = expected.get("account_health")

    if expected_health:
        actual_health = output.get("account_health", {})

        for field, expected_value in expected_health.items():
            checks[f"account_health.{field}"] = (
                actual_health.get(field) == expected_value
            )

    # --------------------------------------------------------
    # Recent tickets
    # --------------------------------------------------------

    expected_ticket_ids = expected.get(
        "recent_ticket_ids"
    )

    if expected_ticket_ids is not None:

        actual_tickets = output.get(
            "recent_support_activity",
            [],
        )

        actual_ticket_ids = {
            ticket.get("ticket_id")
            for ticket in actual_tickets
        }

        checks["recent_tickets"] = all(
            ticket_id in actual_ticket_ids
            for ticket_id in expected_ticket_ids
        )

    # --------------------------------------------------------
    # Risk types
    # --------------------------------------------------------

    expected_risks = expected.get("risk_types")

    if expected_risks is not None:

        actual_risks = output.get(
            "risks",
            [],
        )

        actual_risk_types = {
            risk.get("risk_type")
            for risk in actual_risks
        }

        checks["risk_detection"] = all(
            risk_type in actual_risk_types
            for risk_type in expected_risks
        )

    # --------------------------------------------------------
    # Evidence requirement
    # --------------------------------------------------------

    if expected.get("require_evidence", False):

        risks = output.get("risks", [])

        ticket_risks = [
            risk
            for risk in risks
            if risk.get("source") == "ticket"
        ]

        checks["evidence_present"] = (
            len(ticket_risks) > 0
            and all(
                isinstance(
                    risk.get("evidence_quote"),
                    str,
                )
                and bool(
                    risk.get("evidence_quote").strip()
                )
                for risk in ticket_risks
                if risk.get("risk_type")
                not in {"High Priority Issue"}
            )
        )

    # --------------------------------------------------------
    # Data quality warning
    # --------------------------------------------------------

    if expected.get("require_data_quality_warning", False):

        warnings = output.get(
            "data_quality_warnings",
            [],
        )

        checks["data_quality_warning"] = len(warnings) > 0

    # --------------------------------------------------------
    # Recommended actions
    # --------------------------------------------------------

    if expected.get("require_recommended_actions", False):

        actions = output.get(
            "recommended_actions",
            [],
        )

        checks["recommended_actions"] = (
            isinstance(actions, list)
            and len(actions) > 0
        )

    # --------------------------------------------------------
    # Required structure
    # --------------------------------------------------------

    required_fields = [
        "account_health",
        "recent_support_activity",
        "risks",
        "recommended_actions",
    ]

    checks["valid_structure"] = all(
        field in output
        for field in required_fields
    )

    return {
        "case_id": case["case_id"],
        "task": "Task 2",
        "checks": checks,
    }
