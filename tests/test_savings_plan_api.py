"""
Component tests for /budget-calculator.

The detailed rule variations are covered in test_savings_plan_logic.py;
this file confirms the endpoint wires everything together end-to-end.
"""


def test_budget_calculator_reads_income_and_expenses(client):
    client.post(
        "/income",
        json={
            "source": "Salary",
            "amount": 4000,
            "income_type": "fixed",
            "month": "2026-09-01",
        },
    )
    client.post(
        "/expenses",
        json={"category": "Bills", "amount": 1000, "month": "2026-09-01"},
    )
    client.post(
        "/portfolio",
        json={"account_type": "emergency_fund", "amount": 1600, "date": "2026-09-01"},
    )

    response = client.post(
        "/budget-calculator",
        json={"year": 2026, "month": 9, "emergency_fund_target": 2000},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_income"] == 4000
    assert body["total_expenses"] == 1000
    assert body["disposable_income"] == 3000
    assert body["emergency_fund_contribution"] == 400
    assert body["isa_contribution"] == 2600


def test_budget_calculator_rejects_missing_fields(client):
    response = client.post("/budget-calculator", json={"year": 2026})
    assert response.status_code == 422


def test_savings_plan_endpoint_is_removed(client):
    response = client.post(
        "/savings-plan",
        json={"disposable_income": 1000, "emergency_fund_target": 2000},
    )
    assert response.status_code == 404


def test_budget_calculator_rejects_invalid_month_and_target(client):
    response = client.post(
        "/budget-calculator",
        json={"year": 2026, "month": 13, "emergency_fund_target": -1},
    )
    assert response.status_code == 422
