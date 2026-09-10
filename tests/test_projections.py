from app.projections import Scenario, project_scenario


def test_zero_return_projection_preserves_start_and_contributions():
    result = project_scenario(
        scenario=Scenario("test", 0.0),
        horizon_years=1,
        starting_isa_balance=1000,
        starting_taxable_balance=500,
        monthly_isa_contribution=100,
        monthly_taxable_contribution=0,
        annual_inflation_rate=0.0,
        annual_fee_rate=0.0,
    )

    assert result.ending_nominal_value == 2700.0
    assert result.ending_real_value == 2700.0
    assert result.total_contributions == 1200.0
    assert result.estimated_growth == 0.0
    assert result.estimated_fees == 0.0
    assert result.timeline[-1].year == 1


def test_fixed_scenarios_are_ordered():
    from app.projections import project_all_scenarios

    results = project_all_scenarios(
        horizon_years=10,
        starting_isa_balance=5000,
        starting_taxable_balance=0,
        monthly_isa_contribution=500,
        monthly_taxable_contribution=0,
        annual_inflation_rate=0.025,
        annual_fee_rate=0.0025,
    )

    assert [result.name for result in results] == [
        "conservative",
        "base",
        "optimistic",
    ]
    assert results[0].ending_nominal_value < results[1].ending_nominal_value
    assert results[1].ending_nominal_value < results[2].ending_nominal_value
    assert all(len(result.timeline) == 10 for result in results)


def test_fees_reduce_projected_value():
    from app.projections import Scenario

    without_fees = project_scenario(
        scenario=Scenario("test", 0.05),
        horizon_years=5,
        starting_isa_balance=10000,
        starting_taxable_balance=0,
        monthly_isa_contribution=0,
        monthly_taxable_contribution=0,
        annual_inflation_rate=0.0,
        annual_fee_rate=0.0,
    )
    with_fees = project_scenario(
        scenario=Scenario("test", 0.05),
        horizon_years=5,
        starting_isa_balance=10000,
        starting_taxable_balance=0,
        monthly_isa_contribution=0,
        monthly_taxable_contribution=0,
        annual_inflation_rate=0.0,
        annual_fee_rate=0.01,
    )

    assert with_fees.ending_nominal_value < without_fees.ending_nominal_value
    assert with_fees.estimated_fees > 0


def test_projection_api_returns_scenarios_and_timeline(client):
    response = client.post(
        "/projections",
        json={
            "horizon_years": 2,
            "starting_balances": {"isa": 5000, "taxable_investments": 0},
            "monthly_contributions": {"isa": 500, "taxable_investments": 0},
            "assumptions": {"inflation_rate": 2.5, "annual_fee_rate": 0.25},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["starting_balance"] == 5000
    assert body["total_contributions"] == 12000
    assert [scenario["name"] for scenario in body["scenarios"]] == [
        "conservative",
        "base",
        "optimistic",
    ]
    assert len(body["scenarios"][0]["timeline"]) == 2


def test_projection_api_rejects_invalid_inputs(client):
    response = client.post(
        "/projections",
        json={
            "horizon_years": 0,
            "starting_balances": {"isa": -1, "taxable_investments": 0},
            "monthly_contributions": {"isa": 500, "taxable_investments": 0},
            "assumptions": {"inflation_rate": 2.5, "annual_fee_rate": 0.25},
        },
    )

    assert response.status_code == 422
