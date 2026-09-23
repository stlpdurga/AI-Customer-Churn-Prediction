from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from utils.column_mapper import normalize_target
from services.preprocessing_service import build_features


def train(frame, roles, model_name="Random Forest"):
    target_column = roles.get("churn_target", {}).get("column")
    if not target_column:
        raise ValueError("TARGET_NOT_FOUND")
    y = normalize_target(frame[target_column])
    valid = y.notna()
    if y[valid].nunique() < 2:
        raise ValueError("INSUFFICIENT_CLASSES")
    if valid.sum() < 20:
        raise ValueError("INSUFFICIENT_DATA")
    features, transformer, excluded = build_features(frame.loc[valid], roles)
    model_cls = {"Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
                 "Gradient Boosting": HistGradientBoostingClassifier(max_iter=100, class_weight="balanced"),
                 "Random Forest": RandomForestClassifier(n_estimators=180, random_state=42, class_weight="balanced", n_jobs=-1)}.get(model_name, RandomForestClassifier(n_estimators=180, random_state=42, class_weight="balanced", n_jobs=-1))
    stratify = y[valid] if y[valid].value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(features, y[valid], test_size=0.25, random_state=42, stratify=stratify)
    pipeline = Pipeline([("preprocess", transformer), ("model", model_cls)])
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predicted = (probabilities >= 0.5).astype(int)
    metrics = {"accuracy": round(float(accuracy_score(y_test, predicted)), 4), "precision": round(float(precision_score(y_test, predicted, zero_division=0)), 4),
               "recall": round(float(recall_score(y_test, predicted, zero_division=0)), 4), "f1": round(float(f1_score(y_test, predicted, zero_division=0)), 4),
               "confusion_matrix": confusion_matrix(y_test, predicted).tolist(), "churned": int((y == 1).sum()), "retained": int((y == 0).sum())}
    if len(set(y_test)) == 2:
        metrics["roc_auc"] = round(float(roc_auc_score(y_test, probabilities)), 4)
    return {"pipeline": pipeline, "features": features.columns.tolist(), "excluded": list(excluded), "metrics": metrics}


def predict(frame, roles, trained):
    features, _, _ = build_features(frame, roles)
    probabilities = trained["pipeline"].predict_proba(features)[:, 1]
    result = frame.copy()
    result["churn_probability"] = probabilities.round(4)
    result["risk_level"] = result["churn_probability"].map(lambda value: "High Risk" if value >= 0.70 else "Medium Risk" if value >= 0.40 else "Low Risk")
    return result
