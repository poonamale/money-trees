"""
Unit tests for crud.calculate_budget().

These call the crud function directly with a test database session -
no HTTP requests, no FastAPI routing involved. This is the right
level to test the actual allocation RULES at, since it's faster and
more precise than testing through the API: if one of these fails,
you know the bug is in the calculation logic itself, not in request
validation or routing.
"""

from datetime import date
from app import crud, models, schemas


def _add_contribution(db_session, account_type, amount, contribution_date):
    crud.create_portfolio_contribution(
        db_session,
        schemas.PortfolioContributionCreate(
            account_type=account_type, amount=amount, date=contribution_date
        ),
    )


def _add_budget_inputs(db_session, income, expenses=0):
    crud.create_income(
        db_session,
        schemas.IncomeCreate(
            source="Salary",
            amount=income,
            income_type=schemas.IncomeType.fixed,
            month=date(2026, 9, 1),
        ),
    )
    if expenses:
        crud.create_expense(
            db_session,
            schemas.ExpenseCreate(
                category="Bills", amount=expenses, month=date(2026, 9, 1)
            ),
        )


def test_50_50_split_when_far_under_target(db_session):
    # Emergency fund is empty, target is high - 50% of disposable
    # income won't come close to overshooting it.
    _add_budget_inputs(db_session, income=1000)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=5000)
    assert plan.emergency_fund_contribution == 500
    assert plan.isa_contribution == 500


def test_caps_emergency_contribution_at_remaining_gap(db_session):
    # This is the bug you caught manually: balance is close to
    # target, so 50% would overshoot it.
    _add_contribution(
        db_session, models.AccountType.emergency_fund, 1600, date(2026, 9, 1)
    )
    _add_budget_inputs(db_session, income=3000)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=2000)
    assert plan.emergency_fund_contribution == 400
    assert plan.isa_contribution == 2600


def test_100_percent_isa_once_target_already_met(db_session):
    _add_contribution(
        db_session, models.AccountType.emergency_fund, 2000, date(2026, 9, 1)
    )
    _add_budget_inputs(db_session, income=1000)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=2000)
    assert plan.emergency_fund_contribution == 0
    assert plan.isa_contribution == 1000


def test_isa_overflow_redirects_to_other_investment(db_session):
    # Already close to the £20k annual ISA allowance.
    _add_contribution(db_session, models.AccountType.isa, 19500, date(2026, 9, 1))
    _add_contribution(
        db_session, models.AccountType.emergency_fund, 5000, date(2026, 9, 1)
    )
    _add_budget_inputs(db_session, income=2000)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=1000)
    # Target already met, so all £2000 is "desired" for the ISA - but
    # only £500 of allowance is left, so £1500 should overflow.
    assert plan.isa_contribution == 500
    assert plan.future_savings_contribution == 1500


def test_isa_contribution_before_tax_year_start_not_counted(db_session):
    # A contribution dated before 6 April this tax year shouldn't
    # count toward THIS year's allowance usage, even though it still
    # counts toward the account's total balance.
    _add_contribution(db_session, models.AccountType.isa, 5000, date(2025, 1, 1))
    _add_budget_inputs(db_session, income=1000)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=0)
    assert plan.isa_contributions_this_tax_year == 0
    assert plan.isa_allowance_remaining == 20_000


def test_zero_disposable_income_gives_all_zero_breakdown(db_session):
    _add_budget_inputs(db_session, income=0)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=2000)
    assert plan.emergency_fund_contribution == 0
    assert plan.isa_contribution == 0
    assert plan.future_savings_contribution == 0


def test_overspending_produces_no_recommended_contributions(db_session):
    _add_budget_inputs(db_session, income=1000, expenses=1200)
    plan = crud.calculate_budget(db_session, 2026, 9, emergency_fund_target=2000)

    assert plan.disposable_income == -200
    assert plan.savings_rate == 0
    assert plan.emergency_fund_contribution == 0
    assert plan.isa_contribution == 0
    assert plan.future_savings_contribution == 0
