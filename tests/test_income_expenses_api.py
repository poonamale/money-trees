"""
Component tests for /income, /expenses, and /summary.

Unlike the unit tests, these go through actual HTTP requests via the
TestClient - so they're also checking request validation, routing,
and response serialization, not just the underlying logic.
"""


def test_add_income_returns_the_created_entry(client):
    response = client.post(
        "/income",
        json={
            "source": "Salary",
            "amount": 3000,
            "income_type": "fixed",
            "month": "2026-09-01",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "Salary"
    assert body["amount"] == 3000
    assert "id" in body


def test_add_expense_returns_the_created_entry(client):
    response = client.post(
        "/expenses",
        json={"category": "Rent", "amount": 1200, "month": "2026-09-01"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "Rent"


def test_summary_combines_income_and_expenses(client):
    client.post(
        "/income",
        json={
            "source": "Salary",
            "amount": 3000,
            "income_type": "fixed",
            "month": "2026-09-01",
        },
    )
    client.post(
        "/income",
        json={
            "source": "Freelance",
            "amount": 500,
            "income_type": "variable",
            "month": "2026-09-01",
        },
    )
    client.post(
        "/expenses",
        json={"category": "Rent", "amount": 1200, "month": "2026-09-01"},
    )

    response = client.get("/summary/2026/9")
    assert response.status_code == 200
    body = response.json()
    assert body["total_income"] == 3500
    assert body["total_expenses"] == 1200
    assert body["disposable_income"] == 2300


def test_summary_for_month_with_no_data_returns_zeros(client):
    response = client.get("/summary/2026/1")
    assert response.status_code == 200
    body = response.json()
    assert body["total_income"] == 0
    assert body["total_expenses"] == 0
    assert body["disposable_income"] == 0


def test_add_income_with_invalid_type_is_rejected(client):
    # income_type must be "fixed" or "variable" - anything else
    # should fail FastAPI's validation before it ever reaches crud.py.
    response = client.post(
        "/income",
        json={
            "source": "Salary",
            "amount": 3000,
            "income_type": "not_a_real_type",
            "month": "2026-09-01",
        },
    )
    assert response.status_code == 422
