from pathlib import Path

from data_loader import AccountDataLoader
from risk_detection import RiskDetector


def main():
    project_root = Path(__file__).resolve().parents[2]
    data_root = project_root / "data"

    loader = AccountDataLoader(data_root)

    account_id = "ACC-3336"

    context = loader.get_account_context(account_id)

    detector = RiskDetector()

    risks = detector.detect(
        account=context["account"],
        tickets=context["tickets"],
    )

    print("\n--- ACCOUNT ---")
    print(context["account"]["account_id"])
    print(context["account"]["company"])

    print("\n--- RECENT TICKETS ---")

    for ticket in context["tickets"]:
        print(f"{ticket['ticket_id']} | {ticket['urgency']} | {ticket['subject']}")

    print("\n--- DETECTED RISKS ---")

    for index, risk in enumerate(risks, start=1):
        print(f"\nRisk {index}")
        print(f"Type: {risk['risk_type']}")
        print(f"Severity: {risk['severity']}")
        print(f"Source: {risk['source']}")
        print(f"Reason: {risk['reason']}")

        if risk["source"] == "ticket":
            print(f"Ticket: {risk['ticket_id']}")
        if "evidence_quote" in risk:
            print(f"Evidence: {risk['evidence_quote']}")


if __name__ == "__main__":
    main()
