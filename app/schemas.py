"""
Pydantic schemas - these define the shape of data going in and out of
your API (request bodies and response bodies).

Pydantic is doing double duty here: it validates incoming data (e.g.
rejects a request where "amount" is a string instead of a number)
and it's what FastAPI uses to auto-generate the interactive docs
you'll see at /docs.
"""

from pydantic import BaseModel
from datetime import date
from enum import Enum


class IncomeType(str, Enum):
    fixed = "fixed"
    variable = "variable"


class IncomeCreate(BaseModel):
    source: str
    amount: float
    income_type: IncomeType
    month: date


class IncomeOut(IncomeCreate):
    id: int

    class Config:
        from_attributes = True  # lets Pydantic build this directly from a SQLAlchemy object


class ExpenseCreate(BaseModel):
    category: str
    amount: float
    month: date
    note: str | None = None


class ExpenseOut(ExpenseCreate):
    id: int

    class Config:
        from_attributes = True


class MonthlySummary(BaseModel):
    month: date
    total_income: float
    total_expenses: float
    disposable_income: float

class AccountType(str, Enum):
    emergency_fund = "emergency_fund"
    isa = "isa"
    other_investment = "other_investment"


class PortfolioContributionCreate(BaseModel):
    account_type: AccountType
    amount: float
    date: date


class PortfolioContributionOut(PortfolioContributionCreate):
    id: int

    class Config:
        from_attributes = True


class SavingsPlanRequest(BaseModel):
    disposable_income: float
    emergency_fund_target: float


class SavingsPlanResponse(BaseModel):
    emergency_fund_balance: float
    emergency_fund_target: float
    emergency_fund_contribution: float
    isa_contributions_this_tax_year: float
    isa_allowance_remaining: float
    isa_contribution: float
    other_investment_contribution: float
    
class PortfolioSummary(BaseModel):
    emergency_fund_balance: float
    isa_balance: float
    other_investment_balance: float
    isa_contributions_this_tax_year: float