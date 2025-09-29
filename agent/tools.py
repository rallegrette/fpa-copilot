# agent/tools.py
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

def _read_csv(fname: str) -> pd.DataFrame:
    path = FIXTURES / fname
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def _read_excel_sheets(xlsx_path: Path):
    import pandas as pd
    xl = pd.ExcelFile(xlsx_path)

    def get(sheet_name):
        if sheet_name not in xl.sheet_names:
            raise ValueError(f"Missing sheet '{sheet_name}' in {xl.sheet_names}")
        return xl.parse(sheet_name)

    actuals = get("actuals")
    budget  = get("budget")
    cash    = get("cash")
    fx      = get("fx")

    # --- normalize columns to expected names ---
    def norm(df):
        df = df.copy()
        df.columns = [str(c).strip().lower() for c in df.columns]
        # common renames
        rename_map = {
            "month": "date",
            "account_category": "account",
            "rate_to_usd": "usd_rate",
            "cash_usd": "cash_balance",
        }
        for k, v in rename_map.items():
            if k in df.columns and v not in df.columns:
                df.rename(columns={k: v}, inplace=True)
        # parse date from 'month'
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        return df

    actuals = norm(actuals)
    budget  = norm(budget)
    fx      = norm(fx)
    cash    = norm(cash)

    # cash sheet has no currency; it's already USD
    if "currency" not in cash.columns:
        cash["currency"] = "USD"

    # sanity checks
    need = {
        "actuals": ["date", "entity", "account", "currency", "amount"],
        "budget":  ["date", "entity", "account", "currency", "amount"],
        "fx":      ["date", "currency", "usd_rate"],
        "cash":    ["date", "entity", "currency", "cash_balance"],
    }
    sheets = {"actuals": actuals, "budget": budget, "fx": fx, "cash": cash}
    for key, reqs in need.items():
        missing = [c for c in reqs if c not in sheets[key].columns]
        if missing:
            raise ValueError(f"{key} sheet missing columns: {missing}")

    return actuals, budget, fx, cash


def load_data():
    xlsx = FIXTURES / "data.xlsx"
    if xlsx.exists():
        return _read_excel_sheets(xlsx)
    actuals = _read_csv("actuals.csv")
    budget  = _read_csv("budget.csv")
    fx      = _read_csv("fx.csv")
    cash    = _read_csv("cash.csv")
    return actuals, budget, fx, cash

# ---------- metrics/helpers below ----------

def to_usd(df: pd.DataFrame, fx: pd.DataFrame, amount_col: str) -> pd.DataFrame:
    merged = df.merge(fx, on=["date", "currency"], how="left")
    merged["usd_amount"] = merged[amount_col] * merged["usd_rate"]
    return merged

def monthly_sum_usd(df: pd.DataFrame, fx: pd.DataFrame, amount_col: str, account_prefix: str | None = None) -> pd.DataFrame:
    data = df.copy()
    if account_prefix:
        data = data[data["account"].str.startswith(account_prefix)]
    data = to_usd(data, fx, amount_col)
    data["yyyymm"] = data["date"].dt.to_period("M").astype(str)
    return data.groupby("yyyymm", as_index=False)["usd_amount"].sum()

def revenue_usd(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    return monthly_sum_usd(df, fx, amount_col="amount", account_prefix="Revenue")

def cogs_usd(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    return monthly_sum_usd(df, fx, amount_col="amount", account_prefix="COGS")

def opex_usd(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    return monthly_sum_usd(df, fx, amount_col="amount", account_prefix="Opex")

def opex_breakdown_month(df: pd.DataFrame, fx: pd.DataFrame, month: int, year: int) -> pd.DataFrame:
    data = df[df["account"].str.startswith("Opex:")].copy()
    data = to_usd(data, fx, "amount")
    mask = (data["date"].dt.month == month) & (data["date"].dt.year == year)
    data = data[mask]
    data["category"] = data["account"].str.replace("Opex:", "", regex=False).str.split(":").str[0]
    out = data.groupby("category", as_index=False)["usd_amount"].sum().sort_values("usd_amount", ascending=False)
    return out

def revenue_vs_budget_month(actuals: pd.DataFrame, budget: pd.DataFrame, fx: pd.DataFrame, month: int, year: int) -> dict:
    rev_act = revenue_usd(actuals, fx)
    rev_bud = revenue_usd(budget, fx)
    key = f"{year:04d}-{month:02d}"
    act_val = float(rev_act.loc[rev_act["yyyymm"] == key, "usd_amount"].sum())
    bud_val = float(rev_bud.loc[rev_bud["yyyymm"] == key, "usd_amount"].sum())
    delta = act_val - bud_val
    pct = (delta / bud_val * 100.0) if bud_val else None
    return {"yyyymm": key, "actual_usd": act_val, "budget_usd": bud_val, "delta_usd": delta, "delta_pct": pct}

def gross_margin_trend(actuals: pd.DataFrame, fx: pd.DataFrame, months: int = 3, as_of: datetime | None = None) -> pd.DataFrame:
    as_of = as_of or actuals["date"].max()
    periods = []
    cur = as_of.replace(day=1)
    for _ in range(months):
        periods.append(cur.strftime("%Y-%m"))
        cur = (cur - relativedelta(months=1))
    periods = set(periods)
    rev = revenue_usd(actuals, fx).set_index("yyyymm")
    cogs = cogs_usd(actuals, fx).set_index("yyyymm")
    idx = sorted(list(periods))
    out = []
    for p in idx:
        r = float(rev["usd_amount"].get(p, 0.0))
        c = float(cogs["usd_amount"].get(p, 0.0))
        gm_pct = ((r - c) / r * 100.0) if r else None
        out.append({"yyyymm": p, "gross_margin_pct": gm_pct, "revenue_usd": r, "cogs_usd": c})
    return pd.DataFrame(out)

def ebitda_proxy_month(actuals: pd.DataFrame, fx: pd.DataFrame, month: int, year: int) -> float:
    key = f"{year:04d}-{month:02d}"
    rev = revenue_usd(actuals, fx).set_index("yyyymm")["usd_amount"].get(key, 0.0)
    cogs = cogs_usd(actuals, fx).set_index("yyyymm")["usd_amount"].get(key, 0.0)
    opex = opex_usd(actuals, fx).set_index("yyyymm")["usd_amount"].get(key, 0.0)
    return float(rev - cogs - opex)

def _fx_for_cash(fx: pd.DataFrame, as_of):
    fx = fx.copy()
    fx["yyyymm"] = fx["date"].dt.to_period("M").astype(str)
    month_key = as_of.to_period("M").strftime("%Y-%m")
    month_fx = fx[fx["yyyymm"] == month_key]
    if not month_fx.empty:
        return month_fx.drop(columns=["yyyymm"])
    return fx.sort_values("date").drop(columns=["yyyymm"]).drop_duplicates(subset=["currency"], keep="last")

def cash_runway(cash: pd.DataFrame, actuals: pd.DataFrame, fx: pd.DataFrame, as_of: datetime | None = None) -> dict:
    as_of = as_of or cash["date"].max()
    cash_usd = to_usd(cash, _fx_for_cash(fx, as_of), "cash_balance")
    latest_month = cash_usd["date"].max().to_period("M").strftime("%Y-%m")
    latest_cash = float(
        cash_usd[cash_usd["date"].dt.to_period("M").astype(str) == latest_month]["usd_amount"].sum()
    )
    months = []
    cur = as_of.replace(day=1)
    for _ in range(3):
        months.append((cur.month, cur.year))
        cur = (cur - relativedelta(months=1))
    burns = []
    for m, y in months:
        e = ebitda_proxy_month(actuals, fx, m, y)
        burns.append(-e)
    avg_burn = sum(burns) / len(burns) if burns else 0.0
    runway_months = (latest_cash / avg_burn) if avg_burn > 0 else None
    return {
        "as_of": latest_month,
        "cash_usd": latest_cash,
        "avg_monthly_burn_usd": avg_burn,
        "runway_months": runway_months,
    }
