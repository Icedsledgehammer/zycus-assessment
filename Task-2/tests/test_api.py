from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "TAM Account Health Summariser"


def test_account_brief():
    response = client.get("/accounts/ACC-3336/brief")

    assert response.status_code == 200

    data = response.json()

    # Top-level response structure
    assert "account_health" in data
    assert "recent_support_activity" in data
    assert "risks" in data
    assert "recommended_actions" in data
    assert "data_quality_warnings" in data

    # Account health
    assert data["account_health"]["status"] == "At Risk"
    assert data["account_health"]["usage_trend"] == "Inactive"

    # Recent support activity
    assert len(data["recent_support_activity"]) >= 1

    ticket = data["recent_support_activity"][0]

    assert ticket["ticket_id"] == "TKT-10293"
    assert ticket["product"] == "DataBridge Pro"
    assert ticket["urgency"] == "P2"

    # Risks
    risk_types = {
        risk["risk_type"]
        for risk in data["risks"]
    }

    assert "Account Health" in risk_types
    assert "Usage Inactivity" in risk_types
    assert "Churn" in risk_types
    assert "High Priority Issue" in risk_types
    assert "Operational Impact" in risk_types

    # Data quality warning
    warnings = data["data_quality_warnings"]

    assert len(warnings) >= 1

    assert warnings[0]["type"] == "Company Mismatch"
    assert warnings[0]["ticket_id"] == "TKT-10293"


def test_account_not_found():
    response = client.get("/accounts/ACC-9999/brief")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert "ACC-9999" in data["detail"]


if __name__ == "__main__":
    test_health_check()
    test_account_brief()
    test_account_not_found()

    print("All API tests passed.")
