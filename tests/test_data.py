import pandas as pd
from services.data_service import profile


def test_dynamic_roles_and_quality():
    frame = pd.DataFrame({"client_id": ["a", "b", "b", "c"], "months_active": [2, 4, 4, 8], "monthly_spend": [10, 10, 10, None], "cancelled": ["Yes", "No", "No", "No"]})
    result = profile(frame)
    assert result["roles"]["customer_id"]["column"] == "client_id"
    assert result["roles"]["churn_target"]["column"] == "cancelled"
    assert result["quality"]["duplicates"] == 1
    assert result["quality"]["missing_values"] == 1


def test_target_absent_is_detected():
    result = profile(pd.DataFrame({"customer_number": [1, 2], "revenue": [3, 4]}))
    assert "churn_target" not in result["roles"]
