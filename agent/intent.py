import re
from dataclasses import dataclass

@dataclass
class Intent:
    name: str
    params: dict

MONTHS = {
    'january': 1,'february': 2,'march': 3,'april': 4,'may': 5,'june': 6,
    'july': 7,'august': 8,'september': 9,'october': 10,'november': 11,'december': 12
}

def parse_month_year(text: str):
    text = text.lower()
    for m, idx in MONTHS.items():
        if m in text:
            year_match = re.search(r"(20\d{2})", text)
            return idx, int(year_match.group(1)) if year_match else None
    return None, None

def classify_intent(text: str) -> Intent:
    t = text.lower().strip()
    # Revenue vs budget
    if ("revenue" in t and "budget" in t) or ("vs budget" in t):
        m, y = parse_month_year(t)
        return Intent("revenue_vs_budget", {"month": m, "year": y})
    # Gross margin trend
    if "gross margin" in t and ("trend" in t or "last" in t):
        # pull window if present
        m = re.search(r"last\s+(\d+)", t)
        window = int(m.group(1)) if m else 3
        return Intent("gm_trend", {"months": window})
    # Opex breakdown
    if "opex" in t and ("breakdown" in t or "by category" in t):
        m, y = parse_month_year(t)
        return Intent("opex_breakdown", {"month": m, "year": y})
    # Cash runway
    if "cash runway" in t or ("runway" in t and "cash" in t):
        return Intent("cash_runway", {})
    # Fallback
    return Intent("fallback", {})
