"""Send the same applicant to FastAPI (:8000) and the MLflow scoring server (:5001); compare.
Usage: python compare.py
"""
import requests

applicant = {"income": 1500.0, "loan_amount": 6000.0, "loan_term": 36,
             "credit_score": 700.0, "employment_years": 5}

api = requests.post("http://127.0.0.1:8000/predict", json=applicant, timeout=10).json()
mlf = requests.post("http://127.0.0.1:5001/invocations",
                    json={"dataframe_records": [applicant]}, timeout=10).json()
p_api = api["default_probability"]
p_mlf = mlf["predictions"][0][1]
print("FastAPI      :", p_api)
print("MLflow serve :", round(p_mlf, 6))
print("MATCH" if abs(p_api - p_mlf) < 1e-6 else "DIFFERENT")
