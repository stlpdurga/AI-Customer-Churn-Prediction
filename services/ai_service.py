import os
from services.prompt_service import build_prompt


def generate_insights(summary):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback_insights(summary)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=build_prompt(summary), config={"response_mime_type": "application/json"})
        import json
        return json.loads(response.text)
    except Exception:
        return fallback_insights(summary, unavailable=True)


def fallback_insights(summary, unavailable=False):
    message = "AI insights are temporarily unavailable. Your churn analysis and predictions are still available." if unavailable else "Local insights are based on calculated dataset analytics; configure Gemini for narrative business analysis."
    observations = []
    if summary.get("churn_rate") is not None:
        observations.append({"title": "Observed churn", "observation": f"The uploaded dataset has an observed churn rate of {summary['churn_rate']}%.", "evidence": "Calculated from the detected churn target."})
    if summary.get("risk_distribution"):
        observations.append({"title": "Risk coverage", "observation": f"{summary['risk_distribution']['high']} customers are in the high-risk band.", "evidence": "Model probability thresholds: high >= 0.70."})
    return {"executive_summary": message, "key_observations": observations, "churn_drivers": [], "risk_segments": [], "retention_actions": [{"action": "Review high-risk customers", "reason": "Prioritize outreach using model probability estimates.", "target_segment": "High Risk"}] if summary.get("risk_distribution") else [], "limitations": ["Observed associations do not establish causation.", "Model results depend on the uploaded dataset and available fields."]}
