import pandas as pd
from pathlib import Path

# Locate data.xlsx whether it's at ./fixtures/data.xlsx or ./data.xlsx
root = Path(__file__).resolve().parents[1]
candidates = [root / "fixtures" / "data.xlsx", root / "data.xlsx"]

xlsx = None
for p in candidates:
    if p.exists():
        xlsx = p
        break

if not xlsx:
    raise SystemExit("Could not find data.xlsx. Put it at ./fixtures/data.xlsx or ./data.xlsx")

print("Using:", xlsx)
xl = pd.ExcelFile(xlsx)
print("Sheets:", xl.sheet_names)
for s in xl.sheet_names:
    df = xl.parse(s)
    print(f"\n[{s}] columns ->", [str(c) for c in df.columns])
    print(df.head(3))
