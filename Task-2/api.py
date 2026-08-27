from pathlib import Path

from fastapi import FastAPI, HTTPException

from data_loader import AccountDataLoader
from risk_detection import RiskDetector
from summarizer import TAMSummarizer
from brief_builder import build_final_brief


app = FastAPI(
    title="TAM Account Health Summariser",
    description="Task 2 - US Delivery Internship Technical Task",
    version="1.0.0",
)


# ---------------------------------------------------------
# Paths and components
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"

loader = AccountDataLoader(DATA_ROOT)
risk_detector = RiskDetector()
summarizer = TAMSummarizer()


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "TAM Account Health Summariser",
    }


# ---------------------------------------------------------
# Account TAM brief
# ---------------------------------------------------------

@app.get("/accounts/{account_id}/brief")
def get_account_brief(account_id: str):

    try:
        context = loader.get_account_context(
            account_id=account_id,
            days=90,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    account = context["account"]
    tickets = context["tickets"]

    # Detect risks using deterministic rules.
    risks = risk_detector.detect(
        account=account,
        tickets=tickets,
    )

    # Generate only the interpretive portions.
    llm_output = summarizer.generate(
        account=account,
        tickets=tickets,
        risks=risks,
    )

    # Assemble the final response deterministically.
    brief = build_final_brief(
        account=account,
        tickets=tickets,
        risks=risks,
        llm_output=llm_output,
    )

    # Expose dataset inconsistencies separately.
    brief["data_quality_warnings"] = (
        context.get("inconsistencies", [])
    )

    return brief
