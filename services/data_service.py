import pandas as pd
from utils.column_mapper import detect_roles, normalize_target


def read_upload(file_storage):
    extension = file_storage.filename.lower().rsplit(".", 1)[-1]
    frame = pd.read_excel(file_storage) if extension == "xlsx" else pd.read_csv(file_storage)
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("EMPTY_DATASET")
    frame.columns = [str(column).strip() or f"Column {index + 1}" for index, column in enumerate(frame.columns)]
    return frame


def profile(frame):
    roles = detect_roles(frame)
    missing = frame.isna().sum()
    quality = {
        "rows": int(len(frame)), "columns": int(len(frame.columns)),
        "duplicates": int(frame.duplicated().sum()), "missing_values": int(missing.sum()),
        "constant_columns": [str(column) for column in frame.columns if frame[column].nunique(dropna=False) <= 1],
        "high_cardinality_columns": [str(column) for column in frame.columns if frame[column].nunique(dropna=True) / max(len(frame), 1) > 0.9],
        "columns": [{"name": str(column), "dtype": str(frame[column].dtype), "missing": int(missing[column]),
                     "missing_pct": round(float(missing[column] / max(len(frame), 1) * 100), 2),
                     "unique": int(frame[column].nunique(dropna=True))} for column in frame.columns],
    }
    target = roles.get("churn_target", {}).get("column")
    target_values = normalize_target(frame[target]).dropna() if target else pd.Series(dtype="float64")
    quality["target_classes"] = sorted({int(value) for value in target_values})
    return {"quality": quality, "roles": roles, "preview": frame.head(8).fillna("").to_dict(orient="records")}
