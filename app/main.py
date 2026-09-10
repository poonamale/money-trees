"""
Run with (from the money-trees root folder, venv activated):
    uvicorn app.main:app --reload

"""

from datetime import date
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import models, schemas, crud, projections
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


@app.post("/budget-calculator", response_model=schemas.BudgetCalculatorResponse)
def budget_calculator(
    request: schemas.BudgetCalculatorRequest, db: Session = Depends(get_db)
):
    """
    Reads this month's stored income and expenses, then recommends how
    to allocate the resulting disposable income between the emergency
    fund, ISA, and future savings.
    """
    return crud.calculate_budget(
        db, request.year, request.month, request.emergency_fund_target
    )
    
@app.get("/portfolio/summary", response_model=schemas.PortfolioSummary)
def portfolio_summary(db: Session = Depends(get_db)):
    return schemas.PortfolioSummary(
        emergency_fund_balance=crud.get_balance(db, models.AccountType.emergency_fund),
        isa_balance=crud.get_balance(db, models.AccountType.isa),
        other_investment_balance=crud.get_balance(db, models.AccountType.other_investment),
        isa_contributions_this_tax_year=crud.get_isa_contributions_this_tax_year(db),
    )


@app.post("/projections", response_model=schemas.ProjectionResponse)
def projections_calculator(request: schemas.ProjectionRequest):
    """Project investment growth across conservative, base, and optimistic scenarios."""
    results = projections.project_all_scenarios(
        horizon_years=request.horizon_years,
        starting_isa_balance=request.starting_balances.isa,
        starting_taxable_balance=request.starting_balances.taxable_investments,
        monthly_isa_contribution=request.monthly_contributions.isa,
        monthly_taxable_contribution=request.monthly_contributions.taxable_investments,
        annual_inflation_rate=request.assumptions.inflation_rate / 100,
        annual_fee_rate=request.assumptions.annual_fee_rate / 100,
    )
    scenarios = [
        schemas.ProjectionScenario(
            name=result.name,
            annual_return=result.annual_return_rate,
            ending_nominal_value=result.ending_nominal_value,
            ending_real_value=result.ending_real_value,
            total_contributions=result.total_contributions,
            estimated_growth=result.estimated_growth,
            estimated_fees=result.estimated_fees,
            timeline=[schemas.ProjectionTimelinePoint(**point.__dict__) for point in result.timeline],
        )
        for result in results
    ]
    return schemas.ProjectionResponse(
        horizon_years=request.horizon_years,
        starting_balance=(
            request.starting_balances.isa
            + request.starting_balances.taxable_investments
        ),
        total_contributions=scenarios[0].total_contributions,
        scenarios=scenarios,
    )