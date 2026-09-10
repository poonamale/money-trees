"""
Component tests for /portfolio and /portfolio/summary.
"""


def test_add_portfolio_contribution_returns_the_created_entry(client):
    response = client.post(
        "/portfolio",
        json={"account_type": "isa", "amount": 300, "date": "2026-09-07"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["account_type"] == "isa"
    assert body["amount"] == 300


def test_portfolio_summary_reflects_multiple_contributions(client):
    client.post(
        "/portfolio",
        json={"account_type": "emergency_fund", "amount": 500, "date": "2026-09-07"},
    )
    client.post(
        "/portfolio",
        json={"account_type": "isa", "amount": 300, "date": "2026-09-07"},
    )
    client.post(
        "/portfolio",
        json={
            "account_type": "other_investment",
            "amount": 100,
            "date": "2026-09-07",
        },
    )

    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["emergency_fund_balance"] == 500
    assert body["isa_balance"] == 300
    assert body["other_investment_balance"] == 100
    assert body["isa_contributions_this_tax_year"] == 300


def test_portfolio_summary_with_no_contributions_is_all_zero(client):
    response = client.get("/portfolio/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["emergency_fund_balance"] == 0
    assert body["isa_balance"] == 0
    assert body["other_investment_balance"] == 0


def test_invalid_account_type_is_rejected(client):
    response = client.post(
        "/portfolio",
        json={"account_type": "crypto", "amount": 100, "date": "2026-09-07"},
    )
    assert response.status_code == 422
