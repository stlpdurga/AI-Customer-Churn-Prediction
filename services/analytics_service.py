import pandas as pd
from utils.column_mapper import normalize_target


def summarize(frame, roles, predictions=None):
    result = {"total_customers": len(frame)}
    target = roles.get("churn_target", {}).get("column")
    if target:
        labels = normalize_target(frame[target])
        result["churn_rate"] = round(float(labels.mean() * 100), 2) if labels.notna().any() else None
        result["churned_customers"] = int((labels == 1).sum())
    for key in ("monthly_revenue", "total_revenue", "tenure"):
        column = roles.get(key, {}).get("column")
        if column and pd.api.types.is_numeric_dtype(frame[column]):
            result["average_" + key] = round(float(frame[column].mean()), 2)
    if predictions is not None:
        counts = predictions["risk_level"].value_counts()
        result["risk_distribution"] = {"high": int(counts.get("High Risk", 0)), "medium": int(counts.get("Medium Risk", 0)), "low": int(counts.get("Low Risk", 0))}
    return result


def drivers(frame, roles):
    target = roles.get("churn_target", {}).get("column")
    if not target:
        return []
    labels = normalize_target(frame[target])
    overall = labels.mean()
    items = []
    for role, info in roles.items():
        column = info["column"]
        if role == "churn_target" or column not in frame or frame[column].nunique(dropna=True) > 12:
            continue
        grouped = pd.DataFrame({"value": frame[column].astype(str), "label": labels}).dropna().groupby("value")["label"].agg(["mean", "count"])
        grouped = grouped[grouped["count"] >= max(5, len(frame) * 0.02)].sort_values("mean", ascending=False)
        if not grouped.empty and grouped.iloc[0]["mean"] > overall:
            row = grouped.iloc[0]
            items.append({"factor": column, "group": str(grouped.index[0]), "churn_rate": round(float(row["mean"] * 100), 2), "count": int(row["count"]), "overall_rate": round(float(overall * 100), 2)})
    return sorted(items, key=lambda item: item["churn_rate"] - item["overall_rate"], reverse=True)[:8]
