# Capstone runbook (Windows PowerShell)

Repo: `loan-api-mlflow`. Copy everything from the zip into the repo folder (overwrite).
Keep your Module 5 files (train_tracked.py, register.py, monitor.py and so on); they are still evidence.

---
## A. One-time setup

### A1. Export the real champion from MLflow (replaces the placeholder model)
```powershell
.\.venv\Scripts\Activate.ps1
# Terminal 1: mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
python export_champion.py           # writes model/champion.joblib + model/champion.json, pins scikit-learn
pip install -r requirements-dev.txt
pytest -q                           # all tests pass locally
```

### A2. Push to GitHub
```powershell
git add .
git commit -m "Production loan service: API key, CI/CD to Render, spec"
git push
```
The first `deploy` job will fail (no secrets yet). That's expected.

### A3. Create the Render service (once)
1. render.com → **New → Blueprint** → choose `loan-api-mlflow` (it reads `render.yaml`).
   *(or New → Web Service → repo → Runtime **Docker**, Region Singapore, Plan Free, Health check path `/health`)*
2. **Environment → API_KEY**: generate the value locally and paste it there (never into Git):
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Settings → Build & Deploy → Auto-Deploy: Off**, so only the pipeline deploys.
4. **Settings → Deploy Hook**: copy the URL (it's a secret).
5. Note your URL: `https://<name>.onrender.com`

### A4. GitHub secrets and variables
Repo → **Settings → Secrets and variables → Actions**
| Kind | Name | Value |
|---|---|---|
| Secret | `RENDER_DEPLOY_HOOK_URL` | deploy hook URL |
| Secret | `API_KEY` | same key as on Render |
| Variable | `APP_URL` | `https://<name>.onrender.com` (no trailing /) |

### A5. Branch rule
Repo → **Settings → Branches → Add branch ruleset** (or classic rule) for `main`:
- Require a pull request before merging
- Require status checks to pass → add **`test`**
- Block force pushes
📸 Screenshot the rule. Then re-run the workflow: **Actions → ci-cd → Run workflow** and confirm all 3 jobs are green.

---
## B. Evidence

### Step 1: foundations
- 📸 Actions tab: latest run on `main` green (test → deploy → verify).
- Spec vs live:
  ```powershell
  pip install pyyaml
  python compare_spec.py https://<name>.onrender.com
  ```
  Paste the table. Note anything you changed on purpose.

### Step 3: ship one improvement through a PR
```powershell
git checkout -b feat/<short-name>
# make the change + a test for it
git add . ; git commit -m "feat: <what>" ; git push -u origin feat/<short-name>
```
GitHub → **Compare & pull request** → wait for `test` ✅ → **Merge**.
Then Actions → the run on `main`:
- 📸 the pipeline graph (test → deploy → verify)
- 📸 the verify log with `MERGE TO LIVE: NNNs`
- 📸 `https://<name>.onrender.com/health` showing `git_sha` = the merge commit SHA

### Step 4: security
```powershell
$URL = "https://<name>.onrender.com"
$KEY = "<your key>"     # type it in the terminal only; don't save it in a file
curl.exe -s "$URL/health"                                              # 1. health JSON
curl.exe -s -i "$URL/api/v1/predictions"                               # 2. 401
curl.exe -s -H "X-API-Key: $KEY" "$URL/api/v1/predictions"             # 3. [] (or list)
```
Crop the screenshot so the key is not visible.
SSL Labs: https://www.ssllabs.com/ssltest/analyze.html?d=<name>.onrender.com → 📸 the grade.

### Step 5: bad release drill
Follow `docs/DRILL.md`.

The full requirement → evidence list is in `docs/REQUIREMENTS.md`.

### No-secrets check (requirement 7)
```powershell
git grep -n -i -E "api_key\s*=\s*['\"][A-Za-z0-9_-]{16,}|onrender.com/deploy" ; echo "exit: $LASTEXITCODE (1 = nothing found)"
```
Also screenshot an Actions log where secrets show as `***`.
