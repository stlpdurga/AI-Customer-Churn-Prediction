# BizChurn

BizChurn is a production-style Flask application for customer churn prediction and retention intelligence. It accepts arbitrary CSV and XLSX customer datasets, profiles them, infers likely business fields, trains a leakage-aware scikit-learn pipeline when a valid churn target exists, and presents probability estimates with clear limitations.

## Features


## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. New users can create an account, then sign in to access the dashboard. Set a long random value for `FLASK_SECRET_KEY` in `.env`; set `SESSION_COOKIE_SECURE=1` when serving over HTTPS. To enable Gemini narrative insights, place a key in `GEMINI_API_KEY` in `.env`. The key is never sent to the browser and raw customer rows are not included in the prompt.

For Vercel, configure these Environment Variables for the Production environment before deploying:

- `FLASK_SECRET_KEY`: a long random value. This must remain stable so login sessions survive serverless cold starts.
- `DATABASE_URL`: a hosted PostgreSQL connection string, including any required SSL parameters such as `?sslmode=require`.
- `SESSION_COOKIE_SECURE=1`: recommended for HTTPS deployments; this is the default when Vercel is detected.
- `GEMINI_API_KEY`: optional, for AI narrative insights.

Vercel serverless storage is ephemeral, so the local SQLite database is not suitable for account persistence there. Users must sign up once against the deployed app because the local development database is separate from the production PostgreSQL database. The app now fails at startup with a clear configuration error instead of silently using non-persistent SQLite or a random session key.

## Data and modeling

The mapper uses normalized aliases, fuzzy matching, cardinality, and value validation. Churn must be a historical binary-like field such as `Yes/No`, `1/0`, `Churned/Active`, or `Left/Stayed`. Without a suitable target, the app still profiles and explores the data but blocks prediction rather than fabricating it.

Customer IDs and the target are excluded from features. Date fields become calendar features. Preprocessing is fitted only on the training split. Risk is a probability estimate: low `< 0.40`, medium `0.40-0.69`, high `>= 0.70`.

The included sample is clearly synthetic and intentionally contains missing values and duplicate-like records for quality testing. It is a compact checked-in fixture; generate or upload larger datasets as needed.

## API

`GET /login`, `POST /login`, `GET /signup`, `POST /signup`, `GET /logout`, and `GET /dashboard` provide authentication and the protected application entry point. `GET /api/health`, `POST /api/analyze-data`, `POST /api/train-model`, `POST /api/predict-churn`, `POST /api/business-insights`, `GET /api/history`, `POST /api/save-analysis`, `POST /api/export/predictions`, and `POST /api/export/summary` return JSON except file exports. Analysis APIs require an authenticated session; errors include machine-readable codes such as `TARGET_NOT_FOUND`, `INSUFFICIENT_CLASSES`, `FILE_TOO_LARGE`, and `PREPROCESSING_ERROR`.

## Testing

```powershell
pytest -q
```

Tests cover upload validation, missing values, duplicates, dynamic schemas, target absence, insufficient classes, health, and route errors. Customer data is held only in the current process; SQLite stores analysis summaries, not raw uploads. Keep `.env` and the SQLite file out of version control.
