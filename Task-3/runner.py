from pathlib import Path
import sys
from eval_cases import EVALUATION_CASES
from evaluators import evaluate_task1, evaluate_task2
from scoring import calculate_score, calculate_summary
from report import (
    generate_json_report,
    generate_markdown_report,
)

from llm_judge import LLMJudge

TASK3_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TASK3_ROOT.parent
TASK1_ROOT = PROJECT_ROOT / "Task-1"
TASK2_ROOT = PROJECT_ROOT / "Task-2"

def add_project_path(directory: Path):
    path = str(directory)
    if path not in sys.path:
        sys.path.insert(0, path)

# ============================================================
# TASK 1
# ============================================================
def initialize_task1():
    add_project_path(TASK1_ROOT)
    from Retrieval.kb_reader import load_knowledge_base
    from triage import TicketTriager

    knowledge_base = load_knowledge_base(
        PROJECT_ROOT / "knowledge-base"
    )
    return TicketTriager(knowledge_base)

def run_task1(triager, case):
    return triager.triage_ticket(
        case["input"]
    )

# ============================================================
# TASK 2
# ============================================================
def initialize_task2():
    add_project_path(TASK2_ROOT)
    from data_loader import AccountDataLoader
    from risk_detection import RiskDetector
    from summarizer import TAMSummarizer

    loader = AccountDataLoader(
        PROJECT_ROOT / "data"
    )
    detector = RiskDetector()
    summarizer = TAMSummarizer()
    return loader, detector, summarizer

def run_task2(
    loader,
    detector,
    summarizer,
    case,
):
    from brief_builder import build_final_brief

    account_id = case["input"]["account_id"]
    context = loader.get_account_context(
        account_id
    )
    account = context["account"]
    tickets = context["tickets"]

    risks = detector.detect(
        account=account,
        tickets=tickets,
    )
    llm_output = summarizer.generate(
        account=account,
        tickets=tickets,
        risks=risks,
    )

    return build_final_brief(
        account=account,
        tickets=tickets,
        risks=risks,
        llm_output=llm_output,
    )

# ============================================================
# EVALUATION
# ============================================================
def run_all_evaluations():
    print("=" * 60)
    print("TASK 3 EVALUATION HARNESS")
    print("=" * 60)

    print("\nInitializing Task 1...")
    task1 = initialize_task1()
    print("Task 1 initialized.")

    print("\nInitializing Task 2...")
    loader, detector, summarizer = initialize_task2()
    print("Task 2 initialized.")

    print("\nInitializing LLM Judge...")
    llm_judge = LLMJudge()
    print("LLM Judge initialized.")

    print("\n" + "=" * 60)
    print("RUNNING EVALUATION CASES")
    print("=" * 60)

    results = []
    for index, case in enumerate(
        EVALUATION_CASES,
        start=1,
    ):
        print(
            f"\n[{index}/{len(EVALUATION_CASES)}] "
            f"{case['case_id']} - "
            f"{case['description']}"
        )
        try:
            # ------------------------------------------------
            # Execute actual system
            # ------------------------------------------------
            if case["task"] == "Task 1":
                output = run_task1(
                    task1,
                    case,
                )
                evaluation = evaluate_task1(
                    output,
                    case,
                )
            elif case["task"] == "Task 2":
                output = run_task2(
                    loader,
                    detector,
                    summarizer,
                    case,
                )
                evaluation = evaluate_task2(
                    output,
                    case,
                )
            else:
                raise ValueError(
                    f"Unknown task: {case['task']}"
                )

            # ------------------------------------------------
            # Calculate deterministic score
            # ------------------------------------------------
            scored_result = calculate_score(evaluation)
            scored_result["output"] = output

            # --------------------------------------------------------
            # LLM-as-a-Judge
            # --------------------------------------------------------
            try:
                judge_result = llm_judge.judge(
                    case=case,
                    model_output=output,
                )
                scored_result["llm_judge"] = judge_result
                print(
                    f"Gemini Judge: "
                    f"{judge_result['verdict']} | "
                    f"Score: "
                    f"{judge_result['score']:.3f}"
                )
            except Exception as judge_error:
                print(
                    "Gemini Judge ERROR: "
                    f"{type(judge_error).__name__}: "
                    f"{judge_error}"
                )
                scored_result["llm_judge"] = {
                    "score": None,
                    "verdict": "ERROR",
                    "reasoning": str(judge_error),
                }

            results.append(scored_result)

            status = (
                "PASS"
                if scored_result["passed"]
                else "FAIL"
            )
            print(
                f"Result: {status} | "
                f"Score: "
                f"{scored_result['quality_score']:.3f}"
            )

            if not scored_result["passed"]:
                print("Failed checks:")
                for (
                    check_name,
                    passed,
                ) in scored_result[
                    "checks"
                ].items():
                    if not passed:
                        print(
                            f"  - {check_name}"
                        )

        except Exception as exc:
            print(
                f"ERROR: "
                f"{type(exc).__name__}: {exc}"
            )
            results.append(
                {
                    "case_id": case["case_id"],
                    "task": case["task"],
                    "checks": {},
                    "passed": False,
                    "quality_score": 0.0,
                    "error": str(exc),
                }
            )

    # ========================================================
    # SUMMARY
    # ========================================================
    summary = calculate_summary(
        results
    )
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(
        f"Total cases: "
        f"{summary['total_cases']}"
    )
    print(
        f"Passed: "
        f"{summary['passed_cases']}"
    )
    print(
        f"Failed: "
        f"{summary['failed_cases']}"
    )
    print(
        f"Average quality score: "
        f"{summary['average_quality_score']:.3f}"
    )

    # ========================================================
    # REPORTS
    # ========================================================
    reports_dir = (
        TASK3_ROOT / "reports"
    )
    reports_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    json_path = (
        reports_dir
        / "evaluation_report.json"
    )
    markdown_path = (
        reports_dir
        / "evaluation_report.md"
    )

    generate_json_report(
        results,
        summary,
        json_path,
    )
    generate_markdown_report(
        results,
        summary,
        markdown_path,
    )

    print("\nReports generated:")
    print(
        f"JSON: {json_path}"
    )
    print(
        f"Markdown: {markdown_path}"
    )

    return results, summary

if __name__ == "__main__":
    run_all_evaluations()
