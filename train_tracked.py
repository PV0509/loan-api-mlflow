"""Train >= 6 tracked runs across 3 model types and log them to MLflow.
Usage:  export MLFLOW_TRACKING_URI=http://127.0.0.1:5000 ; python train_tracked.py
"""
import warnings

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import infer_signature
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["income", "loan_amount", "loan_term", "credit_score", "employment_years"]
TARGET = "default"
EXPERIMENT = "loan-default"
THRESHOLD = 0.5
warnings.filterwarnings("ignore", message=".*integer column.*")

RUNS = [
    ("logreg", LogisticRegression, {"C": 0.1, "max_iter": 1000}),
    ("logreg", LogisticRegression, {"C": 1.0, "max_iter": 1000}),
    ("logreg", LogisticRegression, {"C": 1.0, "max_iter": 1000, "class_weight": "balanced"}),
    ("random_forest", RandomForestClassifier, {"n_estimators": 100, "max_depth": 6, "random_state": 0}),
    ("random_forest", RandomForestClassifier, {"n_estimators": 200, "max_depth": 10, "random_state": 0}),
    ("random_forest", RandomForestClassifier, {"n_estimators": 200, "max_depth": 8,
                                               "class_weight": "balanced", "random_state": 0}),
    ("gradient_boosting", GradientBoostingClassifier, {"n_estimators": 150, "max_depth": 3,
                                                       "learning_rate": 0.1, "random_state": 0}),
]


def trusted_types(pipe):
    """Newer MLflow saves sklearn models with skops, which blocks tree types
    (RandomForest/GradientBoosting) unless trusted. We trained this model ourselves
    in this script, so its types are safe to trust."""
    try:
        import skops.io as sio
        return {"skops_trusted_types": sio.get_untrusted_types(data=sio.dumps(pipe))}
    except ImportError:          # older MLflow without skops: nothing to do
        return {}


def main():
    df = pd.read_csv("data/loans.csv")
    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=0)

    mlflow.set_experiment(EXPERIMENT)
    for model_type, cls, params in RUNS:
        run_name = f"{model_type}-" + "-".join(f"{k}{v}" for k, v in params.items()
                                               if k not in ("max_iter", "random_state"))
        with mlflow.start_run(run_name=run_name):
            pipe = Pipeline([("scale", StandardScaler()), ("clf", cls(**params))])
            pipe.fit(X_train, y_train)
            proba = pipe.predict_proba(X_test)[:, 1]
            pred = (proba >= THRESHOLD).astype(int)
            metrics = {
                "recall": recall_score(y_test, pred),
                "precision": precision_score(y_test, pred, zero_division=0),
                "f1": f1_score(y_test, pred),
                "roc_auc": roc_auc_score(y_test, proba),
                "accuracy": accuracy_score(y_test, pred),
            }
            mlflow.set_tag("model_type", model_type)
            mlflow.log_params({"model_type": model_type, "threshold": THRESHOLD, **params})
            mlflow.log_metrics(metrics)
            sig = infer_signature(X_train, pipe.predict_proba(X_train.head(5)))
            mlflow.sklearn.log_model(
                pipe,
                name="model",
                signature=sig,
                input_example=X_train.head(2),
                pyfunc_predict_fn="predict_proba",   # scoring server returns probabilities
                **trusted_types(pipe),
            )
            print(f"{run_name:55s} " + "  ".join(f"{k}={v:.3f}" for k, v in metrics.items()))


if __name__ == "__main__":
    main()