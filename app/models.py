"""
SQLAlchemy models - these define your database tables.

Think of each class below as a table, and each attribute as a column.
This is separate from schemas.py on purpose: models.py describes what's
stored in the database, schemas.py (next file) describes what the API
accepts and returns. They often look similar but serve different jobs -
keeping them apart means you can change your API shape without touching
your database, and vice versa.
"""

from sqlalchemy import Column, Integer, String, Float, Date, Enum
import enum
from .database import Base


class IncomeType(str, enum.Enum):
    fixed = "fixed"
    variable = "variable"


class Income(Base):
    __tablename__ = "income"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)           # e.g. "Salary", "Freelance"
    amount = Column(Float, nullable=False)
    income_type = Column(Enum(IncomeType), nullable=False)
    month = Column(Date, nullable=False)               # store as first-of-month, e.g. 2026-09-01


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)          # e.g. "Rent", "Groceries", "Subscriptions"
    amount = Column(Float, nullable=False)
    month = Column(Date, nullable=False)
    note = Column(String, nullable=True)

class AccountType(str, enum.Enum):
    emergency_fund = "emergency_fund"
    isa = "isa"
    other_investment = "other_investment"   # for money that overflows the ISA allowance


class PortfolioContribution(Base):
    """
    Every time money is put into the emergency fund, ISA, or a general
    investment account, it gets logged as a row here - rather than
    storing one running total. This makes two things easy later:
      - balance = sum of all rows for that account_type
      - "contributions this tax year" = sum of rows filtered by date
    Both are just queries, not numbers we have to remember to update
    or reset manually.
    """
    __tablename__ = "portfolio_contributions"

    id = Column(Integer, primary_key=True, index=True)
    account_type = Column(Enum(AccountType), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)