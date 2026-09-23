import re
from difflib import SequenceMatcher

ROLE_ALIASES = {
    "customer_id": ["customer id", "customerid", "client id", "client number", "account number", "user id"],
    "churn_target": ["churn", "churned", "cancelled", "canceled", "left", "retained", "customer status", "status"],
    "date": ["date", "signup date", "join date", "created", "start date"],
    "age": ["age", "customer age"],
    "tenure": ["tenure", "months active", "subscription length", "months with company", "relationship length"],
    "monthly_revenue": ["monthly revenue", "monthly spend", "monthly charges", "mrr"],
    "total_revenue": ["total revenue", "total charges", "lifetime value", "total spend", "revenue"],
    "usage": ["usage", "data usage", "minutes used", "sessions", "activity"],
    "transactions": ["transactions", "orders", "purchases"],
    "contract": ["contract", "contract type"],
    "subscription": ["subscription", "plan", "plan type", "product"],
    "payment_method": ["payment", "payment method", "billing method"],
    "region": ["region", "country", "state", "location"],
    "gender": ["gender", "sex"],
    "support_tickets": ["support tickets", "support calls", "tickets", "complaints", "issues"],
    "login_activity": ["logins", "login activity", "last login", "sessions"],
    "satisfaction": ["satisfaction", "satisfaction score", "csat", "nps"],
    "discount": ["discount", "discount rate"],
}


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower()).strip()


def _score(name, alias):
    normalized = normalize_name(name)
    if normalized == alias:
        return 1.0
    if alias in normalized or normalized in alias:
        return 0.88
    return SequenceMatcher(None, normalized, alias).ratio()


def _looks_like_churn(series):
    values = {str(value).strip().lower() for value in series.dropna().unique()}
    allowed = {"yes", "y", "true", "1", "churned", "left", "cancelled", "canceled", "no", "n", "false", "0", "active", "stayed", "retained"}
    return bool(values) and len(values) <= 8 and len(values) >= 2 and values.issubset(allowed)


def detect_roles(frame):
    roles = {}
    candidates = []
    for column in frame.columns:
        best_role, best_score = None, 0
        for role, aliases in ROLE_ALIASES.items():
            score = max(_score(column, alias) for alias in aliases)
            if score > best_score:
                best_role, best_score = role, score
        unique_ratio = frame[column].nunique(dropna=True) / max(len(frame), 1)
        if best_role == "churn_target" and not _looks_like_churn(frame[column]):
            best_role, best_score = None, 0
        if best_role == "customer_id" and unique_ratio < 0.5:
            best_role, best_score = None, 0
        if best_role and best_score >= 0.62:
            candidates.append((best_role, best_score, column))
    for role, score, column in sorted(candidates, key=lambda item: item[1], reverse=True):
        if role not in roles:
            roles[role] = {"column": column, "confidence": round(score, 2)}
    for column in frame.columns:
        if column in {item["column"] for item in roles.values()}:
            continue
        if frame[column].nunique(dropna=True) == len(frame) and ("id" in normalize_name(column) or "number" in normalize_name(column)):
            roles.setdefault("customer_id", {"column": column, "confidence": 0.7})
    return roles


def normalize_target(series):
    mapping = {"yes": 1, "y": 1, "true": 1, "1": 1, "churned": 1, "left": 1, "cancelled": 1, "canceled": 1,
               "no": 0, "n": 0, "false": 0, "0": 0, "active": 0, "stayed": 0, "retained": 0}
    return series.astype(str).str.strip().str.lower().map(mapping)
