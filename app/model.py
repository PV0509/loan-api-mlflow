"""Loads the champion model that was exported from the MLflow registry at release time."""
import json
import os
import warnings
from pathlib import Path

import joblib
import numpy as np

warnings.filterwarnings("ignore", message="X does not have valid feature names")

FEATURES = ["income", "loan_amount", "loan_term", "credit_score", "employment_years"]
MODEL_DIR = Path(os.getenv("MODEL_DIR", Path(__file__).resolve().parent.parent / "model"))

_model = joblib.load(MODEL_DIR / "champion.joblib")
INFO = json.loads((MODEL_DIR / "champion.json").read_text())
THRESHOLD = float(os.getenv("DECISION_THRESHOLD", INFO.get("threshold", 0.5)))


def predict_default_probability(rows: list[dict]) -> list[float]:
    x = np.array([[float(r[f]) for f in FEATURES] for r in rows])
    return [float(p) for p in _model.predict_proba(x)[:, 1]]
def risk_band(prob: float) -> str:
    """Business-friendly label for loan officers."""
    if prob < 0.2:
        return "low"
    if prob < 0.5:
        return "medium"
    return "high"