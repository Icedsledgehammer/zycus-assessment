def calculate_score(evaluation: dict) -> dict:
    """
    Convert individual evaluation checks into a quality score
    between 0 and 1.

    Every check currently has equal weight.
    """

    checks = evaluation.get("checks", {})

    if not checks:
        return {
            **evaluation,
            "passed": False,
            "quality_score": 0.0,
        }

    passed_checks = sum(
        1
        for result in checks.values()
        if result is True
    )

    total_checks = len(checks)

    score = passed_checks / total_checks

    return {
        **evaluation,
        "passed": score == 1.0,
        "quality_score": round(score, 3),
    }


def calculate_summary(results: list[dict]) -> dict:
    """
    Calculate aggregate evaluation statistics.
    """

    if not results:
        return {
            "total_cases": 0,
            "passed_cases": 0,
            "failed_cases": 0,
            "average_quality_score": 0.0,
        }

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    failed = total - passed

    average_score = sum(
        result["quality_score"]
        for result in results
    ) / total

    return {
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": failed,
        "average_quality_score": round(
            average_score,
            3,
        ),
    }
