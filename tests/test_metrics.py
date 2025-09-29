import pandas as pd
from agent.tools import load_data, revenue_vs_budget_month, gross_margin_trend

def test_revenue_vs_budget_keys():
    actuals, budget, fx, cash = load_data()
    res = revenue_vs_budget_month(actuals, budget, fx, 6, 2025)
    assert set(res.keys()) == {'yyyymm','actual_usd','budget_usd','delta_usd','delta_pct'}

def test_gm_trend_len():
    actuals, budget, fx, cash = load_data()
    df = gross_margin_trend(actuals, fx, months=3, as_of=pd.Timestamp('2025-06-15'))
    assert len(df) == 3
    assert 'gross_margin_pct' in df.columns
