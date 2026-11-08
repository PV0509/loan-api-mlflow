"""Loan default API. Loads the model BY ALIAS from the MLflow registry.
Run: MLFLOW_TRACKING_URI=http://127.0.0.1:5000 uvicorn main:app --port 8000
(Module 4 Docker image: if MODEL_PATH is set and MODEL_URI is not, loads the baked-in file instead.)
"""
import os

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

FEATURES = ["income", "loan_amount", "loan_term", "credit_score", "employment_years"]
MODEL_PATH = os.getenv("MODEL_PATH")
MODEL_URI = os.getenv("MODEL_URI") or (None if MODEL_PATH else "models:/loan-default@champion")

if MODEL_URI:
    import mlflow
    from mlflow import MlflowClient

    model = mlflow.pyfunc.load_model(MODEL_URI)
    name, alias = MODEL_URI.removeprefix("models:/").split("@")
    mv = MlflowClient().get_model_version_by_alias(name, alias)
    MODEL_INFO = {"source": "registry", "model_uri": MODEL_URI, "alias": alias,
                  "version": mv.version, "run_id": mv.run_id}

    def predict_proba(df):
        return pd.DataFrame(model.predict(df)).iloc[:, 1].to_numpy()
else:
    import re
    import joblib

    model = joblib.load(MODEL_PATH)
    m = re.search(r"(\d+\.\d+\.\d+)", os.path.basename(MODEL_PATH))
    MODEL_INFO = {"source": "file", "model_path": MODEL_PATH,
                  "model_version": m.group(1) if m else "unknown"}

    def predict_proba(df):
        return model.predict_proba(df.to_numpy())[:, 1]


class Applicant(BaseModel):
    income: float = Field(..., gt=0, examples=[1500.0])
    loan_amount: float = Field(..., gt=0, examples=[6000.0])
    loan_term: int = Field(..., gt=0, examples=[36])
    credit_score: float = Field(..., ge=300, le=850, examples=[700.0])
    employment_years: int = Field(..., ge=0, examples=[5])


app = FastAPI(title="Loan Default API")


@app.get("/health")
def health():
    return {"status": "ok", **MODEL_INFO}


@app.post("/predict")
def predict(a: Applicant):
    df = pd.DataFrame([a.model_dump()])[FEATURES].astype(
        {"income": "float64", "loan_amount": "float64", "loan_term": "int64",
         "credit_score": "float64", "employment_years": "int64"})
    p = float(predict_proba(df)[0])
    return {"default_probability": round(p, 6), "decision": "reject" if p >= 0.5 else "approve",
            **{k: v for k, v in MODEL_INFO.items() if k in ("alias", "version", "model_version")}}
