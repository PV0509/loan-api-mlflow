"""Register the two best runs under 'loan-default', set champion/challenger, add descriptions.
Ranking: recall first (missed defaulters cost the most), then roc_auc.
Usage: python register.py
"""
import mlflow
from mlflow import MlflowClient

NAME = "loan-default"
client = MlflowClient()
exp = client.get_experiment_by_name("loan-default")
runs = client.search_runs([exp.experiment_id],
                          filter_string="metrics.precision >= 0.30",
                          order_by=["metrics.recall DESC", "metrics.roc_auc DESC"],
                          max_results=2)

for alias, run in zip(["champion", "challenger"], runs):
    m = run.data.metrics
    mv = mlflow.register_model(f"runs:/{run.info.run_id}/model", NAME)
    client.set_registered_model_alias(NAME, alias, mv.version)
    client.update_model_version(
        NAME, mv.version,
        description=(f"{alias}: {run.info.run_name} | recall={m['recall']:.3f} "
                     f"precision={m['precision']:.3f} roc_auc={m['roc_auc']:.3f} | "
                     f"run {run.info.run_id}"))
    print(f"{alias:10s} -> version {mv.version}  {run.info.run_name}  "
          f"recall={m['recall']:.3f} precision={m['precision']:.3f} auc={m['roc_auc']:.3f}")

client.update_registered_model(NAME, description="Predicts probability that a loan applicant defaults. "
                               "Served by alias: models:/loan-default@champion")
