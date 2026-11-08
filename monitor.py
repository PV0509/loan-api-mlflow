"""Drift monitoring: PSI of each feature (and of the predicted default probability)
for each production week vs the training data. Saves monitor.png + monitor.csv.
Usage: python monitor.py            (prediction drift uses models:/loan-default@champion if MLflow is reachable)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEATURES = ["income", "loan_amount", "loan_term", "credit_score", "employment_years"]
WARN, ALERT = 0.10, 0.25   # set from the chart: see report


def psi(ref, cur, bins=10):
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, edges)[0] / len(ref)
    c = np.histogram(cur, edges)[0] / len(cur)
    r, c = np.clip(r, 1e-4, None), np.clip(c, 1e-4, None)
    return float(np.sum((c - r) * np.log(c / r)))


def main():
    train = pd.read_csv("data/loans.csv")
    prod = pd.read_csv("data/production.csv")
    cols = list(FEATURES)

    try:
        import mlflow
        model = mlflow.pyfunc.load_model("models:/loan-default@champion")
        score = lambda d: pd.DataFrame(model.predict(d[FEATURES])).iloc[:, 1].to_numpy()
        train["pred"] = score(train)
        prod["pred"] = np.concatenate([score(g) for _, g in prod.groupby("week", sort=True)])
        cols.append("pred")
    except Exception as e:
        print("prediction drift skipped:", e)

    rows = [{"week": w, **{c: psi(train[c], g[c]) for c in cols}} for w, g in prod.groupby("week")]
    res = pd.DataFrame(rows).set_index("week")
    res.round(4).to_csv("monitor.csv")
    print(res.round(3).to_string())

    fig, ax = plt.subplots(figsize=(9, 5))
    for c in cols:
        ax.plot(res.index, res[c], marker="o", lw=2.5 if c == "pred" else 1.5,
                label="predicted default prob." if c == "pred" else c)
    ax.axhline(WARN, ls="--", color="orange", label=f"warn PSI={WARN}")
    ax.axhline(ALERT, ls="--", color="red", label=f"alert PSI={ALERT}")
    ax.set(xlabel="production week", ylabel="PSI vs training data",
           title="Feature & prediction drift (PSI) per week")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig("monitor.png", dpi=150)

    latest = res.iloc[-1]
    for c, v in latest.items():
        level = "ALERT" if v >= ALERT else "WARN" if v >= WARN else "ok"
        print(f"week {res.index[-1]} {c:18s} PSI={v:.3f}  {level}")


if __name__ == "__main__":
    main()
