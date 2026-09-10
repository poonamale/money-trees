import os
from datetime import date

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
SCENARIO_COLORS = ["#174f3b", "#6d9c78", "#c48b42"]


def money(value):
    return f"£{value:,.2f}"


def api_request(method, path, payload=None):
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", json=payload, timeout=8)
    except requests.RequestException as error:
        st.error(f"Could not reach the API at {API_BASE_URL}: {error}")
        return None
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        st.error(f"API request failed ({response.status_code}): {detail}")
        return None
    return response.json()


def month_start(selected_month):
    return selected_month.replace(day=1).isoformat()


def load_budget(year, month, emergency_target):
    return api_request("POST", "/budget-calculator", {
        "year": year, "month": month, "emergency_fund_target": emergency_target,
    })


def render_metric_row(metrics):
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)


def render_monthly_money():
    st.markdown("##### 01 · Monthly money")
    st.caption("Build a clear picture of this month before deciding where your money goes next.")
    selected_month = st.date_input("Planning month", value=date.today().replace(day=1), key="budget_month")
    year, month = selected_month.year, selected_month.month
    metrics = st.columns(3)
    metrics[0].metric("Annual gross", "Not available", help="The API currently stores take-home income only.")
    metrics[1].metric("Month", selected_month.strftime("%B %Y"))
    metrics[2].metric("API status", "Connected" if API_BASE_URL else "Not set")

    income_column, expense_column = st.columns(2)
    with income_column:
        with st.form("income_form", clear_on_submit=True, border=True):
            st.markdown("**Take-home income**")
            income_source = st.text_input("Income source", placeholder="Salary")
            income_amount = st.number_input("Monthly take-home income", min_value=0.0, step=50.0)
            income_type = st.selectbox("Income type", ["fixed", "variable"])
            if st.form_submit_button("Save income", type="primary"):
                if not income_source.strip():
                    st.warning("Enter an income source.")
                elif api_request("POST", "/income", {
                    "source": income_source.strip(), "amount": income_amount,
                    "income_type": income_type, "month": month_start(selected_month),
                }):
                    st.success("Income saved.")
    with expense_column:
        with st.form("expense_form", clear_on_submit=True, border=True):
            st.markdown("**Monthly expenses**")
            expense_category = st.text_input("Expense category", placeholder="Rent")
            expense_amount = st.number_input("Monthly expense", min_value=0.0, step=25.0)
            expense_note = st.text_input("Note", placeholder="Optional")
            if st.form_submit_button("Save expense", type="primary"):
                if not expense_category.strip():
                    st.warning("Enter an expense category.")
                elif api_request("POST", "/expenses", {
                    "category": expense_category.strip(), "amount": expense_amount,
                    "month": month_start(selected_month), "note": expense_note.strip() or None,
                }):
                    st.success("Expense saved.")

    st.markdown("**Income → expenses → available to save**")
    emergency_target = st.number_input("Emergency fund target", min_value=0.0, value=6000.0, step=500.0, key="monthly_emergency_target")
    if st.button("Refresh monthly numbers", type="secondary"):
        st.session_state["budget"] = load_budget(year, month, emergency_target)
        st.session_state["portfolio"] = api_request("GET", "/portfolio/summary")
    budget = st.session_state.get("budget")
    if budget and budget.get("month", "").startswith(f"{year:04d}-{month:02d}"):
        render_metric_row([
            ("Income", money(budget["total_income"]), "Stored take-home income"),
            ("Expenses", money(budget["total_expenses"]), "Stored monthly expenses"),
            ("Available to save", money(max(budget["disposable_income"], 0)), "Calculated by the API"),
        ])
    else:
        st.info("Add income and expenses, then refresh to see your monthly position.")


def render_allocation():
    st.markdown("##### 02 · Monthly allocation")
    st.caption("Your allocation is calculated by the API from available savings and account targets.")
    budget = st.session_state.get("budget")
    portfolio = st.session_state.get("portfolio", {})
    if not budget:
        st.info("Refresh monthly numbers above to load your allocation.")
    else:
        rows = [
            ("Emergency fund", budget["emergency_fund_contribution"], portfolio.get("emergency_fund_balance", 0), "Target top-up"),
            ("ISA & investments", budget["isa_contribution"], portfolio.get("isa_balance", 0), "Tax-advantaged contribution"),
            ("Short-term goals", budget["future_savings_contribution"], portfolio.get("other_investment_balance", 0), "Future savings contribution"),
        ]
        for label, contribution, balance, note in rows:
            with st.container(border=True):
                left, middle, right = st.columns([2, 1, 1])
                left.markdown(f"**{label}**\n\n{note}")
                middle.metric("This month", money(contribution))
                right.metric("Current balance", money(balance))


def render_what_if():
    st.markdown("##### 03 · What-if allocation")
    st.caption("Change only the emergency-fund target and let the API recalculate the split.")
    selected_month = st.session_state.get("budget_month", date.today().replace(day=1))
    low_target, high_target = st.columns(2)
    with low_target:
        lower = st.number_input("Lower emergency-fund target", min_value=0.0, value=3000.0, step=500.0)
    with high_target:
        higher = st.number_input("Higher emergency-fund target", min_value=0.0, value=9000.0, step=500.0)
    if st.button("Compare allocations", type="primary"):
        st.session_state["allocation_results"] = [
            ("Lower target", lower, load_budget(selected_month.year, selected_month.month, lower)),
            ("Higher target", higher, load_budget(selected_month.year, selected_month.month, higher)),
        ]
    results = st.session_state.get("allocation_results", [])
    if results:
        columns = st.columns(2)
        for column, (label, target, result) in zip(columns, results):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{label} · {money(target)}**")
                    if result:
                        render_metric_row([
                            ("Emergency fund", money(result["emergency_fund_contribution"]), "API recommendation"),
                            ("ISA", money(result["isa_contribution"]), "API recommendation"),
                            ("Short-term goals", money(result["future_savings_contribution"]), "API recommendation"),
                        ])
    else:
        st.caption("Choose two targets to compare the API recommendations.")


def render_projection():
    st.markdown("##### 04 · Future projection")
    st.caption("Illustrative deterministic scenarios, not guaranteed investment outcomes.")
    horizon = st.segmented_control("Projection horizon", [5, 10, 20], default=10, format_func=lambda value: f"{value} years")
    value_mode = st.segmented_control("Value view", ["Nominal", "Real"], default="Nominal")
    first, second = st.columns(2)
    with first:
        starting_isa = st.number_input("Starting ISA balance", min_value=0.0, value=5000.0, step=500.0)
        monthly_isa = st.number_input("Monthly ISA contribution", min_value=0.0, value=500.0, step=50.0)
        inflation = st.number_input("Inflation rate (%)", min_value=0.0, max_value=100.0, value=2.5, step=0.1)
    with second:
        starting_taxable = st.number_input("Starting taxable investments", min_value=0.0, value=0.0, step=500.0)
        monthly_taxable = st.number_input("Monthly taxable contribution", min_value=0.0, value=0.0, step=50.0)
        fees = st.number_input("Annual fees (%)", min_value=0.0, max_value=100.0, value=0.25, step=0.05)
    if st.button("Run projection", type="primary"):
        st.session_state["projection"] = api_request("POST", "/projections", {
            "horizon_years": horizon, "starting_balances": {"isa": starting_isa, "taxable_investments": starting_taxable},
            "monthly_contributions": {"isa": monthly_isa, "taxable_investments": monthly_taxable},
            "assumptions": {"inflation_rate": inflation, "annual_fee_rate": fees},
        })
    projection = st.session_state.get("projection")
    if projection:
        value_key = "nominal_value" if value_mode == "Nominal" else "real_value"
        chart_rows = [
            {"Year": point["year"], "Scenario": scenario["name"].title(), "Value": point[value_key]}
            for scenario in projection["scenarios"] for point in scenario["timeline"]
        ]
        chart = pd.DataFrame(chart_rows).pivot(index="Year", columns="Scenario", values="Value")
        st.line_chart(chart, color=SCENARIO_COLORS)
        cards = st.columns(len(projection["scenarios"]))
        ending_key = "ending_nominal_value" if value_mode == "Nominal" else "ending_real_value"
        for column, scenario in zip(cards, projection["scenarios"]):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{scenario['name'].title()}**")
                    st.metric("Ending value", money(scenario[ending_key]))
                    st.caption(f"Return {scenario['annual_return']:.1f}% · Growth {money(scenario['estimated_growth'])} · Fees {money(scenario['estimated_fees'])}")


def render_goals():
    st.markdown("##### 05 · Financial goals")
    st.caption("Prototype only: goals live in this browser session and are not persisted to the API.")
    st.session_state.setdefault("goals", [])
    with st.form("goal_form", clear_on_submit=True, border=True):
        goal_name = st.text_input("Goal name", placeholder="Home deposit")
        goal_target = st.number_input("Target amount", min_value=0.0, step=500.0)
        goal_saved = st.number_input("Already saved", min_value=0.0, step=100.0)
        if st.form_submit_button("Add goal", type="primary"):
            if goal_name.strip():
                st.session_state["goals"].append({"name": goal_name.strip(), "target": goal_target, "saved": goal_saved})
                st.rerun()
            st.warning("Enter a goal name.")
    if st.session_state["goals"]:
        columns = st.columns(min(3, len(st.session_state["goals"])))
        for column, goal in zip(columns * ((len(st.session_state["goals"]) + len(columns) - 1) // len(columns)), st.session_state["goals"]):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{goal['name']}**")
                    st.metric("Progress", f"{goal['saved'] / goal['target'] * 100:.0f}%" if goal["target"] else "0%")
                    st.caption(f"{money(goal['saved'])} of {money(goal['target'])}")
    else:
        st.caption("Your prototype goals will appear here.")


def render_ask_money_trees():
    st.markdown("##### 06 · Ask Money Trees")
    st.caption("AI responses are not connected yet. Suggested prompts are placeholders for a future experience.")
    prompts = ["How could I reach my emergency-fund target?", "What should I prioritise this month?", "How does inflation change my projection?"]
    for prompt in prompts:
        st.button(prompt, key=f"prompt_{prompt}", disabled=True)
    st.text_area("Your question", placeholder="Ask a question when this feature is available.", disabled=True)


def main():
    st.set_page_config(page_title="Money Trees", page_icon=":material/account_balance_wallet:", layout="wide")
    st.session_state.setdefault("budget", None)
    st.session_state.setdefault("allocation_results", [])
    st.session_state.setdefault("projection", None)
    st.title("Money Trees", icon=":material/account_balance_wallet:")
    st.caption("A calmer view of what your money is doing now, and where it could go next.")
    st.caption(f"Connected API: {API_BASE_URL}")
    with st.container(border=True):
        st.markdown("##### Welcome to your money plan")
        st.write("Start with this month's take-home income and expenses. We will turn the result into a practical allocation and a longer-term view.")
    with st.container(border=True):
        render_monthly_money()
    with st.container(border=True):
        render_allocation()
    with st.container(border=True):
        render_what_if()
    with st.container(border=True):
        render_projection()
    with st.container(border=True):
        render_goals()
    with st.container(border=True):
        render_ask_money_trees()


if __name__ == "__main__":
    main()
