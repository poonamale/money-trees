"""
Unit tests for current_tax_year_start().

These don't touch the database or the API at all - just calling a
plain function with different dates and checking the output. This is
the simplest, fastest kind of test to write, and a good one to lean
on for tricky date-boundary logic like this, since it's very easy to
be off by one day without realizing.
"""

from datetime import date
from app.utils import current_tax_year_start


def test_after_this_years_april_6():
    # Well after the boundary - should return this year's date.
    assert current_tax_year_start(date(2026, 9, 7)) == date(2026, 4, 6)


def test_before_this_years_april_6():
    # Early in the calendar year, before the UK tax year has "ticked
    # over" yet - should return LAST year's 6 April.
    assert current_tax_year_start(date(2026, 2, 1)) == date(2025, 4, 6)


def test_exactly_on_april_6():
    # The boundary day itself counts as the start of the new tax year.
    assert current_tax_year_start(date(2026, 4, 6)) == date(2026, 4, 6)


def test_day_before_april_6():
    # One day earlier should still be the previous tax year.
    assert current_tax_year_start(date(2026, 4, 5)) == date(2025, 4, 6)
