"""
Small helpers that don't belong to a specific model or route.
"""

from datetime import date


def current_tax_year_start(today: date | None = None) -> date:
    """
    The UK tax year runs 6 April to 5 April. Given today's date,
    return the date the *current* tax year started.

    Example: if today is 2026-09-07, the current tax year started
    on 2026-04-06 (since we're past 6 April this year).
    If today is 2026-02-01, the current tax year actually started
    on 2025-04-06 (we haven't hit this year's 6 April yet).
    """
    if today is None:
        today = date.today()

    this_years_start = date(today.year, 4, 6)

    if today >= this_years_start:
        return this_years_start
    else:
        return date(today.year - 1, 4, 6)
