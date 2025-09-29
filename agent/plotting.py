import plotly.graph_objects as go

def bar_actual_vs_budget(title: str, actual: float, budget: float):
    fig = go.Figure()
    fig.add_bar(name="Actual", x=[""], y=[actual])
    fig.add_bar(name="Budget", x=[""], y=[budget])
    fig.update_layout(barmode="group", title=title, yaxis_title="USD")
    return fig

def line_gm_trend(df):
    fig = go.Figure()
    fig.add_scatter(x=df["yyyymm"], y=df["gross_margin_pct"], mode="lines+markers", name="GM %")
    fig.update_layout(title="Gross Margin % Trend", yaxis_title="%")
    return fig

def pie_opex_breakdown(df, title="Opex Breakdown"):
    fig = go.Figure(data=[go.Pie(labels=df["category"], values=df["usd_amount"], hole=0.35)])
    fig.update_layout(title=title)
    return fig
