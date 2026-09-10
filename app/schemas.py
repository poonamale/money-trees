"""
Pydantic schemas - these define the shape of data going in and out of
your API (request bodies and response bodies).

Pydantic is doing double duty here: it validates incoming data (e.g.
rejects a request where "amount" is a string instead of a number)
and it's what FastAPI uses to auto-generate the interactive docs
you'll see at /docs.
"""

from pydantic import BaseModel, Field
from datetime import date
from enum import Enum


class IncomeType(str, Enum):
    fixed = "fixed"
    variable = "variable"


class IncomeCreate(BaseModel):
    source: str
    amount: float = Field(ge=0)
    income_type: IncomeType
    month: date


class IncomeOut(IncomeCreate):
    id: int

    class Config:
        from_attributes = True  # lets Pydantic build this directly from a SQLAlchemy object


class ExpenseCreate(BaseModel):
    category: str
    amount: float = Field(ge=0)
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
    amount: float = Field(ge=0)
    date: date


class PortfolioContributionOut(PortfolioContributionCreate):
    id: int

    class Config:
        from_attributes = True


class BudgetCalculatorRequest(BaseModel):
    year: int = Field(ge=1)
    month: int = Field(ge=1, le=12)
    emergency_fund_target: float = Field(ge=0)


class BudgetCalculatorResponse(BaseModel):
    month: date
    total_income: float
    total_expenses: float
    disposable_income: float
    savings_rate: float
    emergency_fund_balance: float
    emergency_fund_target: float
    emergency_fund_contribution: float
    isa_contributions_this_tax_year: float
    isa_allowance_remaining: float
    isa_contribution: float
    future_savings_contribution: float
    
class PortfolioSummary(BaseModel):
    emergency_fund_balance: float
    isa_balance: float
    other_investment_balance: float
    isa_contributions_this_tax_year: float


class ProjectionStartingBalances(BaseModel):
    isa: float = Field(ge=0)
    taxable_investments: float = Field(ge=0)


class ProjectionMonthlyContributions(BaseModel):
    isa: float = Field(ge=0)
    taxable_investments: float = Field(ge=0)


class ProjectionAssumptions(BaseModel):
    inflation_rate: float = Field(ge=0, le=100)
    annual_fee_rate: float = Field(ge=0, le=100)


class ProjectionRequest(BaseModel):
    horizon_years: int = Field(ge=1, le=100)
    starting_balances: ProjectionStartingBalances
    monthly_contributions: ProjectionMonthlyContributions
    assumptions: ProjectionAssumptions


class ProjectionTimelinePoint(BaseModel):
    year: int
    contributions: float
    nominal_value: float
    real_value: float


class ProjectionScenario(BaseModel):
    name: str
    annual_return: float
    ending_nominal_value: float
    ending_real_value: float
    total_contributions: float
    estimated_growth: float
    estimated_fees: float
    timeline: list[ProjectionTimelinePoint]


class ProjectionResponse(BaseModel):
    horizon_years: int
    starting_balance: float
    total_contributions: float
    scenarios: list[ProjectionScenario]