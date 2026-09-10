"""Pure projection calculations for long-term savings scenarios."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from math import pow


MONEY_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class Scenario:
    name: str
    annual_return_rate: float


SCENARIOS = (
    Scenario("conservative", 0.03),
    Scenario("base", 0.05),
    Scenario("optimistic", 0.07),
)


@dataclass(frozen=True)
class ProjectionPoint:
    year: int
    contributions: float
    nominal_value: float
    real_value: float


@dataclass(frozen=True)
class ProjectionResult:
    name: str
    annual_return_rate: float
    ending_nominal_value: float
    ending_real_value: float
    total_contributions: float
    estimated_growth: float
    estimated_fees: float
    timeline: list[ProjectionPoint]


def _money(value: float) -> float:
    return float(Decimal(str(value)).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP))


def project_scenario(
    *,
    scenario: Scenario,
    horizon_years: int,
    starting_isa_balance: float,
    starting_taxable_balance: float,
    monthly_isa_contribution: float,
    monthly_taxable_contribution: float,
    annual_inflation_rate: float,
    annual_fee_rate: float,
) -> ProjectionResult:
    """Project two investment sleeves using fixed annual assumptions."""
    isa_balance = starting_isa_balance
    taxable_balance = starting_taxable_balance
    monthly_contribution = monthly_isa_contribution + monthly_taxable_contribution
    total_contributions = 0.0
    total_fees = 0.0
    timeline: list[ProjectionPoint] = []

    monthly_return = pow(1 + scenario.annual_return_rate, 1 / 12) - 1
    monthly_fee = pow(1 + annual_fee_rate, 1 / 12) - 1

    for month in range(1, horizon_years * 12 + 1):
        isa_balance += monthly_isa_contribution
        taxable_balance += monthly_taxable_contribution
        total_contributions += monthly_contribution

        combined_before_growth = isa_balance + taxable_balance
        growth = combined_before_growth * monthly_return
        fees = (combined_before_growth + growth) * monthly_fee
        isa_balance += isa_balance * monthly_return
        taxable_balance += taxable_balance * monthly_return
        isa_balance -= isa_balance * monthly_fee
        taxable_balance -= taxable_balance * monthly_fee
        total_fees += fees

        if month % 12 == 0:
            nominal_value = isa_balance + taxable_balance
            years_elapsed = month // 12
            real_value = nominal_value / pow(1 + annual_inflation_rate, years_elapsed)
            timeline.append(
                ProjectionPoint(
                    year=years_elapsed,
                    contributions=_money(total_contributions),
                    nominal_value=_money(nominal_value),
                    real_value=_money(real_value),
                )
            )

    ending_nominal_value = isa_balance + taxable_balance
    starting_balance = starting_isa_balance + starting_taxable_balance
    estimated_growth = ending_nominal_value - starting_balance - total_contributions + total_fees

    return ProjectionResult(
        name=scenario.name,
        annual_return_rate=scenario.annual_return_rate * 100,
        ending_nominal_value=_money(ending_nominal_value),
        ending_real_value=_money(
            ending_nominal_value / pow(1 + annual_inflation_rate, horizon_years)
        ),
        total_contributions=_money(total_contributions),
        estimated_growth=_money(estimated_growth),
        estimated_fees=_money(total_fees),
        timeline=timeline,
    )


def project_all_scenarios(
    *,
    horizon_years: int,
    starting_isa_balance: float,
    starting_taxable_balance: float,
    monthly_isa_contribution: float,
    monthly_taxable_contribution: float,
    annual_inflation_rate: float,
    annual_fee_rate: float,
) -> list[ProjectionResult]:
    return [
        project_scenario(
            scenario=scenario,
            horizon_years=horizon_years,
            starting_isa_balance=starting_isa_balance,
            starting_taxable_balance=starting_taxable_balance,
            monthly_isa_contribution=monthly_isa_contribution,
            monthly_taxable_contribution=monthly_taxable_contribution,
            annual_inflation_rate=annual_inflation_rate,
            annual_fee_rate=annual_fee_rate,
        )
        for scenario in SCENARIOS
    ]
