"""Regression test added after the bad-release drill (inverted decision bug).
The old tests only checked that `decision` was 'approve' or 'reject', so an inverted
rule passed CI and reached production. These tests pin the business rule."""
import importlib

import pytest
from fastapi.testclient import TestClient

SAFE = {"income": 3000, "loan_amount": 3000, "loan_term": 36, "credit_score": 800, "employment_years": 15}
RISKY = {"income": 500, "loan_amount": 20000, "loan_term": 12, "credit_score": 450, "employment_years": 0}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    import app.main as m
    importlib.reload(m)
    return TestClient(m.app)


def test_risky_applicant_is_rejected(client):
    assert client.post("/api/v1/predictions", json=RISKY).json()["decision"] == "reject"


def test_safe_applicant_is_approved(client):
    assert client.post("/api/v1/predictions", json=SAFE).json()["decision"] == "approve"


def test_decision_follows_threshold(client):
    from app import model
    for applicant in (SAFE, RISKY):
        body = client.post("/api/v1/predictions", json=applicant).json()
        expected = "reject" if body["default_probability"] >= model.THRESHOLD else "approve"
        assert body["decision"] == expected
