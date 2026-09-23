import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_features(frame, roles):
    target = roles.get("churn_target", {}).get("column")
    excluded = {target, roles.get("customer_id", {}).get("column")}
    excluded.discard(None)
    features = frame.drop(columns=list(excluded), errors="ignore").copy()
    for column in list(features.columns):
        if roles.get("date", {}).get("column") == column:
            parsed = pd.to_datetime(features[column], errors="coerce")
            features[column + "_year"] = parsed.dt.year
            features[column + "_month"] = parsed.dt.month
            features[column + "_day"] = parsed.dt.day
            features.drop(columns=[column], inplace=True)
    numeric = features.select_dtypes(include="number").columns.tolist()
    categorical = [column for column in features.columns if column not in numeric]
    transformer = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")), ("encode", OneHotEncoder(handle_unknown="ignore"))]), categorical),
    ], remainder="drop")
    return features, transformer, excluded
