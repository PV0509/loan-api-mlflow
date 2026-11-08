"""Release step: export the model currently aliased @champion in the MLflow registry
into model/ so the production image is self-contained (no MLflow server in production).

Usage (with the Module 5 MLflow server running):
    $env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"     # PowerShell
    python export_champion.py
Then commit model/ and open a pull request.
"""
import json
import re
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import sklearn
from mlflow import MlflowClient

NAME, ALIAS = "loan-default", "champion"
out = Path("model")
out.mkdir(exist_ok=True)

client = MlflowClient()
mv = client.get_model_version_by_alias(NAME, ALIAS)
run = client.get_run(mv.run_id)
pipe = mlflow.sklearn.load_model(f"models:/{NAME}@{ALIAS}")

joblib.dump(pipe, out / "champion.joblib")
info = {
    "name": NAME, "alias": ALIAS, "version": mv.version, "run_id": mv.run_id,
    "run_name": run.info.run_name,
    "metrics": {k: round(v, 4) for k, v in run.data.metrics.items()},
    "threshold": float(run.data.params.get("threshold", 0.5)),
    "sklearn_version": sklearn.__version__,
}
(out / "champion.json").write_text(json.dumps(info, indent=2))

# pin the exact scikit-learn version the model was trained with
req = Path("requirements.txt")
req.write_text(re.sub(r"scikit-learn==[\w.]+", f"scikit-learn=={sklearn.__version__}", req.read_text()))
print(json.dumps(info, indent=2))
