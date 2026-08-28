import json
from pathlib import Path


def generate_json_report(
    results: list[dict],
    summary: dict,
    output_path: Path,
):
    report = {
        "summary": summary,
        "results": results,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )


def generate_markdown_report(
    results: list[dict],
    summary: dict,
    output_path: Path,
):
    lines = [
        "# Evaluation Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Total cases | {summary['total_cases']} |",
        f"| Passed | {summary['passed_cases']} |",
        f"| Failed | {summary['failed_cases']} |",
        f"| Average deterministic score | "
        f"{summary['average_quality_score']:.3f} |",
        "",
        "## Evaluation Results",
        "",
        "| Case | Task | Deterministic | Gemini Judge | Verdict |",
        "|---|---|---:|---:|---|",
    ]

    for result in results:

        status = (
            "PASS"
            if result.get("passed")
            else "FAIL"
        )

        judge = result.get("llm_judge")

        if judge and judge.get("score") is not None:
            judge_score = f"{judge['score']:.3f}"
            judge_verdict = judge.get(
                "verdict",
                "UNKNOWN",
            )
        else:
            judge_score = "N/A"
            judge_verdict = "ERROR"

        lines.append(
            f"| {result['case_id']} "
            f"| {result['task']} "
            f"| {status} "
            f"{result['quality_score']:.3f} "
            f"| {judge_score} "
            f"| {judge_verdict} |"
        )

    lines.extend(
        [
            "",
            "## Detailed Evaluation",
            "",
        ]
    )

    for result in results:

        lines.append(
            f"### {result['case_id']} "
            f"({result['task']})"
        )

        lines.append("")

        status = (
            "PASS"
            if result.get("passed")
            else "FAIL"
        )

        lines.append(
            f"**Deterministic result:** "
            f"{status} "
            f"({result['quality_score']:.3f})"
        )

        lines.append("")

        judge = result.get("llm_judge")

        if judge:

            if judge.get("score") is not None:

                lines.append(
                    f"**Gemini Judge:** "
                    f"{judge.get('verdict', 'UNKNOWN')} "
                    f"({judge['score']:.3f})"
                )

                lines.append("")

                lines.append(
                    f"**Judge reasoning:** "
                    f"{judge.get('reasoning', '')}"
                )

            else:

                lines.append(
                    "**Gemini Judge:** ERROR"
                )

                lines.append("")

                lines.append(
                    f"**Judge error:** "
                    f"{judge.get('reasoning', '')}"
                )

        lines.append("")

        if result.get("checks"):

            lines.append(
                "**Deterministic checks:**"
            )

            lines.append("")

            for check, passed in result[
                "checks"
            ].items():

                check_status = (
                    "PASS"
                    if passed
                    else "FAIL"
                )

                lines.append(
                    f"- `{check}`: "
                    f"**{check_status}**"
                )

            lines.append("")

        if result.get("error"):

            lines.append(
                f"**Execution error:** "
                f"`{result['error']}`"
            )

            lines.append("")

    lines.extend(
        [
            "## Evaluation Methodology",
            "",
            "The evaluation combines two complementary "
            "approaches:",
            "",
            "1. **Deterministic evaluation** checks objective "
            "requirements such as expected fields, labels, "
            "risk detection, and data-quality warnings.",
            "2. **Gemini LLM-as-a-Judge** provides an independent "
            "qualitative assessment of factual correctness, "
            "grounding, completeness, interpretation, and "
            "overall usefulness.",
            "",
            "The deterministic evaluator is treated as the "
            "source of truth for hard requirements, while "
            "the LLM judge provides additional semantic "
            "quality assessment.",
            "",
        ]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
