import json
from pathlib import Path

from data_loader import AccountDataLoader
from risk_detection import RiskDetector
from summarizer import TAMSummarizer
from brief_builder import build_final_brief


def main():

    project_root = Path(__file__).resolve().parents[2]
    data_root = project_root / "data"

    account_id = "ACC-3336"

    loader = AccountDataLoader(data_root)

    context = loader.get_account_context(
        account_id=account_id,
        days=90,
    )

    detector = RiskDetector()

    risks = detector.detect(
        account=context["account"],
        tickets=context["tickets"],
    )

    summarizer = TAMSummarizer(model_name="qwen3:4b")

    llm_output = summarizer.generate(
        account=context["account"],
        tickets=context["tickets"],
        risks=risks,
    )

    final_brief = build_final_brief(
        account=context["account"],
        tickets=context["tickets"],
        risks=risks,
        llm_output=llm_output,
    )

    print("\n--- RAW LLM OUTPUT ---\n")
    print(llm_output)

    print("\n--- FINAL TAM BRIEF ---\n")
    print(
        json.dumps(
            final_brief,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
