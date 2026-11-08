"""Generate the loan-default training data and 8 weeks of 'production' data.
Usage: python make_data.py   -> data/loans.csv, data/production.csv
"""
import os
import numpy as np
import pandas as pd

FEATURES = ["income", "loan_amount", "loan_term", "credit_score", "employment_years"]


def applicants(n, rng, income_mu=1200.0, credit_mu=650.0, loan_mu=8000.0):
    df = pd.DataFrame({
        "income": rng.normal(income_mu, 500, n).clip(200, 6000).round(2),
        "loan_amount": rng.normal(loan_mu, 4000, n).clip(500, 40000).round(2),
        "loan_term": rng.choice([12, 24, 36, 48, 60], n).astype("int64"),
        "credit_score": rng.normal(credit_mu, 70, n).clip(300, 850).round(0),
        "employment_years": rng.integers(0, 30, n).astype("int64"),
    })
    return df


def label(df, rng):
    burden = (df.loan_amount / df.loan_term) / df.income          # monthly payment / income
    logit = (-1.2 - 0.015 * (df.credit_score - 650) + 4.0 * (burden - 0.25)
             - 0.06 * df.employment_years + 0.00004 * (df.loan_amount - 8000))
    p = 1 / (1 + np.exp(-logit))
    return (rng.random(len(df)) < p).astype("int64")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    rng = np.random.default_rng(42)
    train = applicants(10000, rng)
    train["default"] = label(train, rng)
    train.to_csv("data/loans.csv", index=False)

    # 8 weekly batches: weeks 1-4 stable, weeks 5-8 drift (incomes fall, credit scores fall, bigger loans)
    batches = []
    for week in range(1, 9):
        shift = max(0, week - 4)
        b = applicants(1000, rng,
                       income_mu=1200 - 70 * shift,
                       credit_mu=650 - 12 * shift,
                       loan_mu=8000 + 600 * shift)
        b.insert(0, "week", week)
        batches.append(b)
    pd.concat(batches).to_csv("data/production.csv", index=False)
    print("train:", train.shape, "default rate:", round(train["default"].mean(), 3))
    print("production:", sum(len(b) for b in batches), "rows over 8 weeks")
