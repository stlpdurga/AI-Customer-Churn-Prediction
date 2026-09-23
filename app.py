import io
import json
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from auth import login_required, register_auth_routes
from database.db import history, init_db, save
from models.churn_model import predict, train
from services.ai_service import generate_insights
from services.analytics_service import drivers, summarize
from services.data_service import profile, read_upload
from utils.validators import validate_upload

load_dotenv()
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or os.urandom(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
STATE = {"frame": None, "profile": None, "trained": None, "predictions": None, "dataset_name": None}

ERRORS = {"TARGET_NOT_FOUND": "Churn prediction requires a historical churn/retention target column. This dataset does not contain a suitable target.",
          "INSUFFICIENT_CLASSES": "Prediction cannot be trained because the dataset does not contain enough examples of both churn classes.",
          "INSUFFICIENT_DATA": "Prediction cannot be trained because there are too few valid labeled records.", "EMPTY_DATASET": "The uploaded dataset is empty."}


def error_response(code, message=None, status=400):
    return jsonify({"error": {"code": code, "message": message or ERRORS.get(code, "The request could not be processed.")}}), status


@app.get("/")
def index():
    return redirect(url_for("dashboard"))


@app.get("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "customer-churn-intelligence"})


@app.post("/api/analyze-data")
@login_required
def analyze_data():
    valid, code, message = validate_upload(request.files.get("file"))
    if not valid:
        return error_response(code, message)
    try:
        frame = read_upload(request.files["file"])
        STATE.update({"frame": frame, "profile": profile(frame), "trained": None, "predictions": None, "dataset_name": request.files["file"].filename})
        return jsonify({"dataset_name": STATE["dataset_name"], **STATE["profile"]})
    except ValueError as exc:
        return error_response(str(exc))
    except Exception:
        return error_response("FILE_INVALID", "The file could not be read as a valid CSV or XLSX dataset.", 422)


@app.post("/api/train-model")
@login_required
def train_model():
    if STATE["frame"] is None:
        return error_response("NO_DATASET", "Upload and analyze a dataset first.")
    try:
        model = train(STATE["frame"], STATE["profile"]["roles"], request.json.get("model", "Random Forest") if request.is_json else "Random Forest")
        STATE["trained"] = model
        return jsonify({"model": request.json.get("model", "Random Forest") if request.is_json else "Random Forest", "metrics": model["metrics"], "excluded_columns": model["excluded"]})
    except ValueError as exc:
        return error_response(str(exc))
    except Exception:
        return error_response("MODEL_TRAINING_ERROR", "The model could not be trained with the available fields.", 422)


@app.post("/api/predict-churn")
@login_required
def predict_churn():
    if STATE["trained"] is None:
        return error_response("PREDICTION_ERROR", "Train a model before generating probabilities.")
    try:
        STATE["predictions"] = predict(STATE["frame"], STATE["profile"]["roles"], STATE["trained"])
        prediction_frame = STATE["predictions"]
        rows = prediction_frame.head(500).fillna("").to_dict(orient="records")
        analytics = summarize(STATE["frame"], STATE["profile"]["roles"], prediction_frame)
        return jsonify({"analytics": analytics, "drivers": drivers(STATE["frame"], STATE["profile"]["roles"]), "rows": rows, "total_rows": len(prediction_frame)})
    except Exception:
        return error_response("PREDICTION_ERROR", "Customer probabilities could not be generated.", 422)


@app.post("/api/business-insights")
@login_required
def business_insights():
    if STATE["frame"] is None:
        return error_response("NO_DATASET", "Analyze a dataset before requesting insights.")
    summary = summarize(STATE["frame"], STATE["profile"]["roles"], STATE["predictions"])
    summary["drivers"] = drivers(STATE["frame"], STATE["profile"]["roles"])
    return jsonify(generate_insights(summary))


@app.get("/api/history")
@login_required
def get_history():
    return jsonify(history())


@app.post("/api/compare")
@login_required
def compare_analyses():
    if STATE["frame"] is None:
        return error_response("NO_DATASET", "Analyze a dataset before comparing it.")
    saved = history()
    if not saved:
        return jsonify({"current": summarize(STATE["frame"], STATE["profile"]["roles"], STATE["predictions"]), "previous": None, "changes": []})
    current = summarize(STATE["frame"], STATE["profile"]["roles"], STATE["predictions"])
    previous = saved[0]["payload"].get("analytics", {})
    comparable = sorted(set(current) & set(previous) - {"risk_distribution"})
    changes = [{"metric": key, "current": current[key], "previous": previous[key], "change": round(float(current[key] - previous[key]), 4)}
               for key in comparable if isinstance(current[key], (int, float)) and isinstance(previous[key], (int, float))]
    return jsonify({"current": current, "previous": previous, "changes": changes})


@app.post("/api/save-analysis")
@login_required
def save_analysis():
    if STATE["frame"] is None:
        return error_response("NO_DATASET", "Analyze a dataset before saving it.")
    payload = {"dataset_name": STATE["dataset_name"], "profile": STATE["profile"], "analytics": summarize(STATE["frame"], STATE["profile"]["roles"], STATE["predictions"]), "model": STATE["trained"]["metrics"] if STATE["trained"] else None}
    return jsonify({"id": save(STATE["dataset_name"], payload)})


def export_frame(frame, filename, mimetype, as_json=False):
    output = io.BytesIO()
    if as_json:
        output.write(json.dumps(frame, default=str, indent=2).encode())
    else:
        output.write(frame.to_csv(index=False).encode())
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=filename, mimetype=mimetype)


@app.post("/api/export/predictions")
@login_required
def export_predictions():
    if STATE["predictions"] is None:
        return error_response("PREDICTION_ERROR", "Generate predictions before exporting.")
    return export_frame(STATE["predictions"], "customer-risk-report.csv", "text/csv")


@app.post("/api/export/summary")
@login_required
def export_summary():
    if STATE["frame"] is None:
        return error_response("NO_DATASET", "Analyze a dataset before exporting.")
    payload = {"dataset_name": STATE["dataset_name"], "profile": STATE["profile"], "analytics": summarize(STATE["frame"], STATE["profile"]["roles"], STATE["predictions"]), "model": STATE["trained"]["metrics"] if STATE["trained"] else None, "generated_at": datetime.utcnow().isoformat()}
    return export_frame(payload, "analytics-summary.json", "application/json", as_json=True)


register_auth_routes(app)
init_db()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
