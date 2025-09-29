import streamlit as st
import pandas as pd
from datetime import datetime
from agent.intent import classify_intent
from agent.tools import load_data, revenue_vs_budget_month, gross_margin_trend, opex_breakdown_month, cash_runway
from agent.plotting import bar_actual_vs_budget, line_gm_trend, pie_opex_breakdown

st.set_page_config(page_title="Mini CFO Copilot", page_icon="📊", layout="centered")
st.title("Mini CFO Copilot")
st.caption("Ask finance questions from CSVs. Returns concise, board-ready answers + charts.")

@st.cache_data
def _load():
    return load_data()

actuals, budget, fx, cash = _load()

q = st.text_input("Ask a question", value="What was June 2025 revenue vs budget in USD?")
if st.button("Ask") or q:
    intent = classify_intent(q)
    st.write(f"**Intent:** `{intent.name}`")
    if intent.name == "revenue_vs_budget":
        month = intent.params.get("month")
        year = intent.params.get("year")
        if not month or not year:
            st.warning("Please include a month and year, e.g., 'June 2025'.")
        else:
            res = revenue_vs_budget_month(actuals, budget, fx, month, year)
            st.metric(label=f"Revenue vs Budget — {res['yyyymm']}", value=f"${res['actual_usd']:,.0f}", delta=f"${res['delta_usd']:,.0f}" + (f" ({res['delta_pct']:.1f}%)" if res['delta_pct'] is not None else ""))
            fig = bar_actual_vs_budget(f"Revenue vs Budget — {res['yyyymm']}", res["actual_usd"], res["budget_usd"])
            st.plotly_chart(fig, use_container_width=True)
    elif intent.name == "gm_trend":
        months = int(intent.params.get("months", 3))
        df = gross_margin_trend(actuals, fx, months=months)
        st.dataframe(df)
        fig = line_gm_trend(df)
        st.plotly_chart(fig, use_container_width=True)
    elif intent.name == "opex_breakdown":
        month = intent.params.get("month")
        year = intent.params.get("year")
        if not month or not year:
            st.warning("Please include a month and year, e.g., 'June 2025'.")
        else:
            df = opex_breakdown_month(actuals, fx, month, year)
            st.dataframe(df)
            st.plotly_chart(pie_opex_breakdown(df, title=f"Opex Breakdown — {year:04d}-{month:02d}"), use_container_width=True)
    elif intent.name == "cash_runway":
        res = cash_runway(cash, actuals, fx)
        if res["runway_months"] is None:
            st.info(f"As of {res['as_of']}, cash is ${res['cash_usd']:,.0f}. No burn detected in last 3 months (or negative).")
        else:
            st.metric(label=f"Cash Runway (as of {res['as_of']})", value=f"{res['runway_months']:.1f} months", delta=f"Cash ${res['cash_usd']:,.0f} | Avg burn ${res['avg_monthly_burn_usd']:,.0f}/mo")
    else:
        st.write("I can help with: Revenue vs Budget, Gross Margin trend, Opex breakdown, Cash runway. Try: 'Show gross margin % trend for the last 3 months.'")

st.markdown("---\n_Data sources read from `fixtures/`. Replace sample CSVs with your own._")
