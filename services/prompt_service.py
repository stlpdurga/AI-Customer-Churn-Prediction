def build_prompt(summary):
    return """Return strict JSON with keys executive_summary, key_observations, churn_drivers, risk_segments, retention_actions, limitations. Use only this structured analytics; never invent values or causation.\n\n""" + str(summary)
