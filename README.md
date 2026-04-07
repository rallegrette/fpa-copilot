# Mini CFO Copilot (FP&A Coding Assignment)

A small Streamlit app that answers CFO-style questions from monthly CSVs and returns concise, board-ready answers with charts.

## Quickstart

1) **Clone** this repo and create a virtual env:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) **Add data** (CSV files) into `fixtures/` with these filenames:
   - `actuals.csv` — columns: `date, entity, account, currency, amount`
   - `budget.csv`  — columns: `date, entity, account, currency, amount`
   - `fx.csv`      — columns: `date, currency, usd_rate` (1 unit of currency * usd_rate = USD)
   - `cash.csv`    — columns: `date, entity, currency, cash_balance`

   You can export the provided spreadsheet to CSV and drop them here.

3) **Run the app:**
```bash
streamlit run app.py
```

4) **Try questions:**
   - "What was June 2025 revenue vs budget?"
   - "Show gross margin % trend for the last 3 months."
   - "Break down opex by category for June 2025."
   - "What is our cash runway right now?"

## Project structure

```text
app.py               # Streamlit UI + agent call
agent/
  intent.py          # rule-based intent classifier
  tools.py           # data loaders + metric functions
  plotting.py        # chart helpers
fixtures/            # sample CSVs (replace with your own)
tests/
  test_metrics.py    # a couple of sanity tests
requirements.txt
README.md
```

## Notes
- Metrics:
  - **Revenue (USD)**: actual vs budget
  - **Gross Margin %**: (Revenue − COGS) / Revenue
  - **Opex total (USD)**: accounts starting with `Opex:` (e.g., `Opex:Sales`)
  - **EBITDA (proxy)**: Revenue − COGS − Opex
  - **Cash runway**: cash ÷ avg monthly net burn (last 3 months)
- Intent classification is simple regex to keep the exercise snappy. You can swap in LLMs later.
- The tests run on the sample fixtures just to prove the plumbing works.
# fpa-copilot
