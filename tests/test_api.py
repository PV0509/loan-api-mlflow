import importlib

import pytest
from fastapi.testclient import TestClient

GOOD = {"income": 1500, "loan_amount": 6000, "loan_term": 36, "credit_score": 700, "employment_years": 5}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    import app.main as m
    importlib.reload(m)
    return TestClient(m.app)


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key-123")
    import app.main as m
    importlib.reload(m)
    return TestClient(m.app)


def test_health_reports_model_and_sha(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_alias"] == "champion"
    assert body["git_sha"]


def test_create_prediction_returns_201_and_location(client):
    r = client.post("/api/v1/predictions", json=GOOD)
    assert r.status_code == 201
    body = r.json()
    assert 0.0 <= body["default_probability"] <= 1.0
    assert body["decision"] in ("approve", "reject")
    assert r.headers["Location"] == f"/api/v1/predictions/{body['id']}"


def test_get_list_and_delete(client):
    pid = client.post("/api/v1/predictions", json=GOOD).json()["id"]
    assert client.get(f"/api/v1/predictions/{pid}").status_code == 200
    assert any(p["id"] == pid for p in client.get("/api/v1/predictions?limit=100").json())
    assert client.delete(f"/api/v1/predictions/{pid}").status_code == 204
    assert client.get(f"/api/v1/predictions/{pid}").status_code == 404


def test_invalid_input_is_422(client):
    bad = {**GOOD, "credit_score": "high"}
    assert client.post("/api/v1/predictions", json=bad).status_code == 422
    missing = {k: v for k, v in GOOD.items() if k != "income"}
    assert client.post("/api/v1/predictions", json=missing).status_code == 422


def test_api_key_three_checks(secured):
    assert secured.get("/health").status_code == 200                        # open front window
    assert secured.get("/api/v1/predictions").status_code == 401            # no key
    assert secured.get("/api/v1/predictions",
                       headers={"X-API-Key": "wrong"}).status_code == 401   # wrong key
    r = secured.get("/api/v1/predictions", headers={"X-API-Key": "test-key-123"})
    assert r.status_code == 200 and isinstance(r.json(), list)


def test_model_ranks_risk_sensibly(client):
    """Model contract: a much riskier applicant must get a higher default probability."""
    safe = {"income": 3000, "loan_amount": 3000, "loan_term": 36, "credit_score": 800, "employment_years": 15}
    risky = {"income": 500, "loan_amount": 20000, "loan_term": 12, "credit_score": 450, "employment_years": 0}
    p_safe = client.post("/api/v1/predictions", json=safe).json()["default_probability"]
    p_risky = client.post("/api/v1/predictions", json=risky).json()["default_probability"]
    assert p_risky > p_safe
