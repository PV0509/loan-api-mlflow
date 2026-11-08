# Module 5 runbook (Codespace, bash terminals)

Copy these files into your loan-api repo root (main.py replaces the old one; it still works for the
Module 4 Docker image because that image sets MODEL_PATH).

```bash
pip install -r requirements-mlflow.txt
python make_data.py                     # data/loans.csv + data/production.csv
```

## Terminal 1: MLflow tracking server (program 1)
```bash
mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db
```
Open the forwarded port 5000 (Ports tab) to see the UI.

## Terminal 2: experiment + register (Steps 1–2)
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
python train_tracked.py                 # 7 runs, 3 model types  -> screenshot table + UI run list
python register.py                      # v1 = champion, v2 = challenger, descriptions set
```
Evidence: UI → Experiments → loan-default (compare runs: recall, precision, roc_auc),
UI → Models → loan-default (both versions with @champion / @challenger and descriptions).
Run link format: `https://<codespace>-5000.app.github.dev/#/experiments/<exp_id>/runs/<run_id>`

## Terminal 3: MLflow scoring server (program 2)
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
mlflow models serve -m "models:/loan-default@champion" -p 5001 --env-manager local
```

## Terminal 4: FastAPI (program 3)
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Step 4: test the scoring server
Valid request (expect 200 + `{"predictions": [[p_no_default, p_default]]}`):
```bash
curl -s -X POST http://127.0.0.1:5001/invocations -H "Content-Type: application/json" \
  -d '{"dataframe_records":[{"income":1500.0,"loan_amount":6000.0,"loan_term":36,"credit_score":700.0,"employment_years":5}]}'
```
Request the signature rejects (credit_score is text, employment_years missing; expect 400 + "Failed to enforce schema"):
```bash
curl -s -i -X POST http://127.0.0.1:5001/invocations -H "Content-Type: application/json" \
  -d '{"dataframe_records":[{"income":1500.0,"loan_amount":6000.0,"loan_term":36,"credit_score":"high"}]}'
```
Same applicant through both servers:
```bash
python compare.py                        # prints both probabilities and MATCH
curl -s http://127.0.0.1:8000/health     # shows source=registry, alias=champion, version, run_id
```

## Step 5: monitor
```bash
python monitor.py                        # table + monitor.png + monitor.csv
```

## Step 6: roll back and forward
```bash
python set_champion.py 2                 # champion -> v2
# Ctrl+C FastAPI in Terminal 4, start it again, then:
curl -s http://127.0.0.1:8000/health     # version "2"
python set_champion.py 1                 # champion -> v1
# restart FastAPI again
curl -s http://127.0.0.1:8000/health     # version "1"
```
The API code never changes: it always loads `models:/loan-default@champion`.
