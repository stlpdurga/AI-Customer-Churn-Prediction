import pandas as pd
import pytest
from models.churn_model import train


def test_insufficient_classes():
    frame = pd.DataFrame({"customer_id": range(25), "age": range(25), "churn": ["No"] * 25})
    with pytest.raises(ValueError, match="INSUFFICIENT_CLASSES"):
        train(frame, {"churn_target": {"column": "churn"}})
