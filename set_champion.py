"""Move an alias to a version (rollback / roll forward).
Usage: python set_champion.py <version> [alias]
"""
import sys
from mlflow import MlflowClient

version = sys.argv[1]
alias = sys.argv[2] if len(sys.argv) > 2 else "champion"
c = MlflowClient()
c.set_registered_model_alias("loan-default", alias, version)
for a in ("champion", "challenger"):
    try:
        print(a, "->", c.get_model_version_by_alias("loan-default", a).version)
    except Exception:
        print(a, "-> (not set)")
