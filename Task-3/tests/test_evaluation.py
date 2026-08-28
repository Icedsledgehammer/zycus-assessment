from evaluators import (
    evaluate_task1,
    evaluate_task2,
)

from scoring import (
    calculate_score,
    calculate_summary,
)


def test_task1_perfect_result():

    case = {
        "case_id": "TEST-T1",
        "expected": {
            "product_area": "Data Ingestion",
            "issue_category": "Feature Request",
            "urgency_tier": "P3",
            "matches_known_knowledge_base_issue": False,
            "relevant_knowledge_base_document": None,
        },
    }

    output = {
        "product_area": "Data Ingestion",
        "issue_category": "Feature Request",
        "urgency_tier": "P3",
        "reasoning": "Test reasoning",
        "matches_known_knowledge_base_issue": False,
        "relevant_knowledge_base_document": None,
        "recommended_responder_team": "Engineering Team",
        "draft_first_response_message": "Thank you.",
    }

    evaluation = evaluate_task1(
        output,
        case,
    )

    result = calculate_score(
        evaluation
    )

    assert result["passed"] is True
    assert result["quality_score"] == 1.0


def test_task1_failed_result():

    case = {
        "case_id": "TEST-T1-FAIL",
        "expected": {
            "issue_category": "Feature Request",
        },
    }

    output = {
        "product_area": "Data Ingestion",
        "issue_category": "Bug",
        "urgency_tier": "P3",
        "reasoning": "Test",
        "matches_known_knowledge_base_issue": False,
        "recommended_responder_team": "Engineering",
        "draft_first_response_message": "Test",
    }

    evaluation = evaluate_task1(
        output,
        case,
    )

    result = calculate_score(
        evaluation
    )

    assert result["passed"] is False
    assert result["quality_score"] < 1.0


def test_task2_risk_detection():

    case = {
        "case_id": "TEST-T2",
        "expected": {
            "account_health": {
                "status": "At Risk",
                "usage_trend": "Inactive",
            },
            "risk_types": [
                "Account Health",
                "Churn",
            ],
            "require_recommended_actions": True,
        },
    }

    output = {
        "account_health": {
            "status": "At Risk",
            "usage_trend": "Inactive",
        },
        "recent_support_activity": [],
        "risks": [
            {
                "risk_type": "Account Health",
            },
            {
                "risk_type": "Churn",
            },
        ],
        "recommended_actions": [
            "Contact customer",
        ],
    }

    evaluation = evaluate_task2(
        output,
        case,
    )

    result = calculate_score(
        evaluation
    )

    assert result["passed"] is True
    assert result["quality_score"] == 1.0


def test_summary():

    results = [
        {
            "case_id": "A",
            "task": "Task 1",
            "passed": True,
            "quality_score": 1.0,
        },
        {
            "case_id": "B",
            "task": "Task 1",
            "passed": False,
            "quality_score": 0.5,
        },
    ]

    summary = calculate_summary(
        results
    )

    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 1
    assert summary["failed_cases"] == 1
    assert summary["average_quality_score"] == 0.75


if __name__ == "__main__":
    test_task1_perfect_result()
    test_task1_failed_result()
    test_task2_risk_detection()
    test_summary()

    print("All evaluation tests passed.")
