"""Loan service: production API.

Open:      GET /health, /docs, /openapi.json
Protected: everything under /api/  (X-API-Key header, only when API_KEY is set)
"""
import hmac
import os

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import model, store

API_KEY = os.getenv("API_KEY")                       # run-time secret (Render env var)
GIT_SHA = os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA", "dev")

app = FastAPI(
    title="Loan Service API",
    version="1.0.0",
    description="Scores loan applicants for probability of default. "
                "All /api/ routes need the X-API-Key header.",
)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    if API_KEY and request.url.path.startswith("/api/"):
        sent = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(sent.encode(), API_KEY.encode()):
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


# ---------- schemas (reused, like components.schemas in the spec) ----------
class Applicant(BaseModel):
    income: float = Field(..., gt=0, le=1_000_000, description="Monthly income (USD)", examples=[1500])
    loan_amount: float = Field(..., gt=0, le=1_000_000, description="Loan amount (USD)", examples=[6000])
    loan_term: int = Field(..., ge=6, le=120, description="Term in months", examples=[36])
    credit_score: float = Field(..., ge=300, le=850, examples=[700])
    employment_years: int = Field(..., ge=0, le=60, examples=[5])


class Prediction(BaseModel):
    id: int
    created_at: str
    applicant: Applicant
    default_probability: float
    decision: str
    model_version: str


class Health(BaseModel):
    status: str
    git_sha: str
    model_name: str
    model_alias: str
    model_version: str


# ---------- routes ----------
@app.get("/health", response_model=Health, tags=["ops"])
def health():
    return {"status": "ok", "git_sha": GIT_SHA,
            "model_name": model.INFO["name"], "model_alias": model.INFO["alias"],
            "model_version": str(model.INFO["version"])}


@app.post("/api/v1/predictions", response_model=Prediction, status_code=201, tags=["predictions"])
def create_prediction(applicant: Applicant, response: Response):
    data = applicant.model_dump()
    prob = model.predict_default_probability([data])[0]
    decision = "reject" if prob >= model.THRESHOLD else "approve"
    pred = store.add(data, round(prob, 6), decision, str(model.INFO["version"]))
    response.headers["Location"] = f"/api/v1/predictions/{pred['id']}"
    return pred


@app.get("/api/v1/predictions", response_model=list[Prediction], tags=["predictions"])
def list_predictions(limit: int = Query(20, ge=1, le=100),
                     after_id: int = Query(0, ge=0, description="Cursor: id of the last item you have")):
    return store.list_(limit, after_id)


@app.get("/api/v1/predictions/{pred_id}", response_model=Prediction, tags=["predictions"])
def get_prediction(pred_id: int):
    pred = store.get(pred_id)
    if not pred:
        raise HTTPException(404, "Prediction not found")
    return pred


@app.delete("/api/v1/predictions/{pred_id}", status_code=204, tags=["predictions"])
def delete_prediction(pred_id: int):
    if not store.delete(pred_id):
        raise HTTPException(404, "Prediction not found")
    return Response(status_code=204)
