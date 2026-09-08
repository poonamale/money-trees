"""
CRUD = Create, Read, Update, Delete.

These functions are the only place that talks directly to the
database. Keeping that logic out of main.py keeps your route
handlers thin and makes this stuff easy to unit test later.
"""

from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from . import models, schemas
from .utils import current_tax_year_start

ISA_ANNUAL_ALLOWANCE = 20_000.0

def create_income(db: Session, income: schemas.IncomeCreate) -> models.Income:
    db_income = models.Income(**income.model_dump())
    db.add(db_income)
    db.commit()
    db.refresh(db_income)  # pulls back the auto-generated id from the DB
    return db_income


def create_expense(db: Session, expense: schemas.ExpenseCreate) -> models.Expense:
    db_expense = models.Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_income_for_month(db: Session, year: int, month: int):
    return (
        db.query(models.Income)
        .filter(
            extract("year", models.Income.month) == year,
            extract("month", models.Income.month) == month,
        )
        .all()
    )


def get_expenses_for_month(db: Session, year: int, month: int):
    return (
        db.query(models.Expense)
        .filter(
            extract("year", models.Expense.month) == year,
            extract("month", models.Expense.month) == month,
        )
        .all()
    )

def create_portfolio_contribution(
    db: Session, contribution: schemas.PortfolioContributionCreate
) -> models.PortfolioContribution:
    db_contribution = models.PortfolioContribution(**contribution.model_dump())
    db.add(db_contribution)
    db.commit()
    db.refresh(db_contribution)
    return db_contribution


def get_balance(db: Session, account_type: models.AccountType) -> float:
    """
    Sums every contribution ever made to a given account type.
    func.sum returns None (not 0) if there are no rows yet, so we
    fall back to 0.0 in that case.
    """
    total = (
        db.query(func.sum(models.PortfolioContribution.amount))
        .filter(models.PortfolioContribution.account_type == account_type)
        .scalar()
    )
    return total or 0.0


def get_isa_contributions_this_tax_year(db: Session) -> float:
    tax_year_start = current_tax_year_start()
    total = (
        db.query(func.sum(models.PortfolioContribution.amount))
        .filter(
            models.PortfolioContribution.account_type == models.AccountType.isa,
            models.PortfolioContribution.date >= tax_year_start,
        )
        .scalar()
    )
    return total or 0.0


def calculate_savings_plan(
    db: Session, disposable_income: float, emergency_fund_target: float
) -> schemas.SavingsPlanResponse:
    """
    The core allocation rule:
      - While the emergency fund is below target: split disposable
        income 50/50 between emergency fund and ISA.
      - Once the emergency fund target is met: send 100% to ISA.
      - Either way, never suggest putting more into the ISA than the
        remaining annual allowance - anything over that is redirected
        to a general (taxable) investment account instead.
    """
    emergency_fund_balance = get_balance(db, models.AccountType.emergency_fund)
    isa_contributions_this_tax_year = get_isa_contributions_this_tax_year(db)
    isa_allowance_remaining = max(
        ISA_ANNUAL_ALLOWANCE - isa_contributions_this_tax_year, 0.0
    )

    if emergency_fund_balance < emergency_fund_target:
        emergency_fund_contribution = min(disposable_income * 0.5, emergency_fund_target - emergency_fund_balance)
        isa_desired = disposable_income - emergency_fund_contribution
    else:
        emergency_fund_contribution = 0.0
        isa_desired = disposable_income

    # Cap the ISA contribution at whatever allowance is left this tax year.
    isa_contribution = min(isa_desired, isa_allowance_remaining)
    other_investment_contribution = isa_desired - isa_contribution

    return schemas.SavingsPlanResponse(
        emergency_fund_balance=emergency_fund_balance,
        emergency_fund_target=emergency_fund_target,
        emergency_fund_contribution=emergency_fund_contribution,
        isa_contributions_this_tax_year=isa_contributions_this_tax_year,
        isa_allowance_remaining=isa_allowance_remaining,
        isa_contribution=isa_contribution,
        other_investment_contribution=other_investment_contribution,
    )