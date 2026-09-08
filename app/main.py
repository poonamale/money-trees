"""
Run with (from the money-trees root folder, venv activated):
    uvicorn app.main:app --reload

"""

from datetime import date
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, get_db

# Creates the income/expenses tables in money_trees.db if they don't
# already exist. Safe to run every time the app starts.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Money Trees", description="Personal finance coach API")


@app.get("/")
def root():
    return {"message": "Money Trees API is running"}


@app.post("/income", response_model=schemas.IncomeOut)
def add_income(income: schemas.IncomeCreate, db: Session = Depends(get_db)):
    return crud.create_income(db, income)


@app.post("/expenses", response_model=schemas.ExpenseOut)
def add_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, expense)

@app.get("/summary/{year}/{month}", response_model=schemas.MonthlySummary)
def monthly_summary(year: int, month: int, db: Session = Depends(get_db)):
    """
    Returns total income, total expenses, and disposable income
    (what's left to save/invest) for a given month.

    Example: GET /summary/2026/9
    """
    income_entries = crud.get_income_for_month(db, year, month)
    expense_entries = crud.get_expenses_for_month(db, year, month)

    total_income = sum(i.amount for i in income_entries)
    total_expenses = sum(e.amount for e in expense_entries)

    return schemas.MonthlySummary(
        month=date(year, month, 1),
        total_income=total_income,
        total_expenses=total_expenses,
        disposable_income=total_income - total_expenses,
    )

@app.post("/portfolio", response_model=schemas.PortfolioContributionOut)
def add_portfolio_contribution(
    contribution: schemas.PortfolioContributionCreate, db: Session = Depends(get_db)
):
    """
    Log a contribution to the emergency fund, ISA, or a general
    investment account. Example body:
        { "account_type": "isa", "amount": 200, "date": "2026-09-07" }
    """
    return crud.create_portfolio_contribution(db, contribution)


@app.post("/savings-plan", response_model=schemas.SavingsPlanResponse)
def savings_plan(request: schemas.SavingsPlanRequest, db: Session = Depends(get_db)):
    """
    Given this month's disposable income and your emergency fund
    target, returns how much to put into the emergency fund vs ISA
    (50/50 until the target is met, then 100% ISA) - capped at
    whatever ISA allowance you have left for the current tax year.
    """
    return crud.calculate_savings_plan(
        db, request.disposable_income, request.emergency_fund_target
    )
    
@app.get("/portfolio/summary", response_model=schemas.PortfolioSummary)
def portfolio_summary(db: Session = Depends(get_db)):
    return schemas.PortfolioSummary(
        emergency_fund_balance=crud.get_balance(db, models.AccountType.emergency_fund),
        isa_balance=crud.get_balance(db, models.AccountType.isa),
        other_investment_balance=crud.get_balance(db, models.AccountType.other_investment),
        isa_contributions_this_tax_year=crud.get_isa_contributions_this_tax_year(db),
    )