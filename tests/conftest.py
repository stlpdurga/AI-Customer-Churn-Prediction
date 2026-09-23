import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, STATE


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "history.db"))
    STATE.update({"frame": None, "profile": None, "trained": None, "predictions": None, "dataset_name": None})
    app.config["TESTING"] = True
    return app.test_client()
