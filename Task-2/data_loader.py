import json
from datetime import datetime, timedelta
from pathlib import Path


class AccountDataLoader:
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)

        self.accounts_path = self.data_root / "accounts.json"
        self.tickets_path = self.data_root / "tickets.json"

        self.accounts = self._load_json(self.accounts_path)
        self.tickets = self._load_json(self.tickets_path)

    @staticmethod
    def _load_json(file_path: Path):
        with file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def get_account(self, account_id: str):
        for account in self.accounts:
            if account.get("account_id") == account_id:
                return account

        return None

    def get_recent_tickets(
        self,
        account_id: str,
        days: int = 90,
    ):
        account_tickets = [
            ticket
            for ticket in self.tickets
            if ticket.get("account_id") == account_id
        ]

        if not account_tickets:
            return []

        # Use the latest ticket timestamp as the dataset reference point.
        latest_date = max(
            datetime.fromisoformat(
                ticket["created_at"].replace("Z", "+00:00")
            )
            for ticket in account_tickets
        )

        cutoff_date = latest_date - timedelta(days=days)

        recent_tickets = [
            ticket
            for ticket in account_tickets
            if datetime.fromisoformat(
                ticket["created_at"].replace("Z", "+00:00")
            ) >= cutoff_date
        ]

        recent_tickets.sort(
            key=lambda ticket: ticket["created_at"]
        )

        return recent_tickets

    def find_account_data_inconsistencies(
        self,
        account: dict,
        tickets: list[dict],
    ) -> list[dict]:

        inconsistencies = []

        account_id = account.get("account_id")
        account_company = account.get("company")

        for ticket in tickets:

            if ticket.get("account_id") != account_id:
                continue

            ticket_company = ticket.get("company")

            if (
                ticket_company
                and account_company
                and ticket_company != account_company
            ):
                inconsistencies.append(
                    {
                        "type": "Company Mismatch",
                        "ticket_id": ticket.get("ticket_id"),
                        "account_id": account_id,
                        "account_company": account_company,
                        "ticket_company": ticket_company,
                    }
                )

        return inconsistencies

    def get_account_context(
        self,
        account_id: str,
        days: int = 90,
    ):
        account = self.get_account(account_id)

        if account is None:
            raise ValueError(
                f"Account not found: {account_id}"
            )

        tickets = self.get_recent_tickets(
            account_id=account_id,
            days=days,
        )

        inconsistencies = self.find_account_data_inconsistencies(
            account,
            tickets,
        )

        return {
            "account": account,
            "tickets": tickets,
            "period_days": days,
            "inconsistencies": inconsistencies,
        }


if __name__ == "__main__":

    project_root = Path(__file__).resolve().parents[1]
    data_root = project_root / "data"

    loader = AccountDataLoader(data_root)

    account_id = "ACC-3336"

    context = loader.get_account_context(
        account_id=account_id,
        days=90,
    )

    print("Account:")
    print(context["account"])

    print(
        f"\nTickets in last "
        f"{context['period_days']} days:"
    )

    print(
        f"Count: {len(context['tickets'])}"
    )

    for ticket in context["tickets"]:
        print(
            f"{ticket['ticket_id']} | "
            f"{ticket['created_at']} | "
            f"{ticket['urgency']} | "
            f"{ticket['subject']}"
        )

    if context["inconsistencies"]:

        print("\nData Inconsistencies:")

        for inconsistency in context["inconsistencies"]:
            print(inconsistency)

    else:
        print("\nData Inconsistencies:")
        print("None")
