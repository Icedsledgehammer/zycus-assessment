from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"


def load_json(filename):
    with (DATA_ROOT / filename).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def find_ticket(tickets, ticket_id):
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket

    raise ValueError(
        f"Ticket not found: {ticket_id}"
    )


def find_account(accounts, account_id):
    for account in accounts:
        if account["account_id"] == account_id:
            return account

    raise ValueError(
        f"Account not found: {account_id}"
    )


def build_evaluation_cases():

    tickets = load_json("tickets.json")
    accounts = load_json("accounts.json")

    # ========================================================
    # TASK 1
    # ========================================================

    task1_cases = [
        {
            "case_id": "T1-01",
            "task": "Task 1",
            "description": "Feature request with no relevant KB information",
            "input": find_ticket(
                tickets,
                "TKT-10000",
            ),
            "expected": {
                "product_area": "Data Ingestion",
                "issue_category": "Feature Request",
                "urgency_tier": "P2",
                "matches_known_knowledge_base_issue": False,
            },
        },

        {
            "case_id": "T1-02",
            "task": "Task 1",
            "description": "Authentication or SSO issue",
            "input": find_ticket(
                tickets,
                "TKT-10003",
            ),
            "expected": {
                "issue_category": "How-To",
            },
        },

        {
            "case_id": "T1-03",
            "task": "Task 1",
            "description": "Bug report",
            "input": find_ticket(
                tickets,
                "TKT-10006",
            ),
            "expected": {
                "issue_category": "Bug",
            },
        },

        {
            "case_id": "T1-04",
            "task": "Task 1",
            "description": "Feature request / performance-related ticket",
            "input": find_ticket(
                tickets,
                "TKT-10008",
            ),
            "expected": {
                "issue_category": "Feature Request",
            },
        },

        {
            "case_id": "T1-05",
            "task": "Task 1",
            "description": "Billing-related ticket",
            "input": find_ticket(
                tickets,
                "TKT-10013",
            ),
            "expected": {
                "issue_category": "Billing",
            },
        },
    ]

    # ========================================================
    # TASK 2
    # ========================================================

    task2_cases = [
        {
            "case_id": "T2-01",
            "task": "Task 2",
            "description": (
                "Healthy account with increasing usage "
                "and no open tickets"
            ),
            "input": {
                "account_id": "ACC-1664",
            },
            "expected": {
                "account_health": {
                    "status": "Healthy",
                    "usage_trend": "Increasing",
                },
                "require_recommended_actions": True,
            },
        },

        {
            "case_id": "T2-02",
            "task": "Task 2",
            "description": (
                "At-risk account with inactive usage "
                "and churn signal"
            ),
            "input": {
                "account_id": "ACC-3336",
            },
            "expected": {
                "account_health": {
                    "status": "At Risk",
                    "usage_trend": "Inactive",
                },
                "risk_types": [
                    "Account Health",
                    "Usage Inactivity",
                    "Churn",
                ],
                "require_recommended_actions": True,
            },
        },

        {
            "case_id": "T2-03",
            "task": "Task 2",
            "description": (
                "Churning account with declining usage"
            ),
            "input": {
                "account_id": "ACC-2944",
            },
            "expected": {
                "account_health": {
                    "status": "Churning",
                    "usage_trend": "Declining",
                },
                "require_recommended_actions": True,
            },
        },

        {
            "case_id": "T2-04",
            "task": "Task 2",
            "description": (
                "Healthy account with high support volume"
            ),
            "input": {
                "account_id": "ACC-3033",
            },
            "expected": {
                "account_health": {
                    "status": "Healthy",
                    "usage_trend": "Increasing",
                },
                "require_recommended_actions": True,
            },
        },

        {
            "case_id": "T2-05",
            "task": "Task 2",
            "description": (
                "Account containing deliberate source-data "
                "inconsistency"
            ),
            "input": {
                "account_id": "ACC-3336",
            },
            "expected": {
                "account_health": {
                    "status": "At Risk",
                    "usage_trend": "Inactive",
                },
                "require_data_quality_warning": True,
                "require_recommended_actions": True,
            },
        },
    ]

    return task1_cases + task2_cases


EVALUATION_CASES = build_evaluation_cases()
