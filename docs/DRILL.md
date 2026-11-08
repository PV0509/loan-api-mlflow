# Bad release drill

**Scenario:** a refactor of the decision line accidentally flips the rule, so risky applicants
get **approved**. The current tests only check that `decision` is "approve" or "reject", so CI is
green and the pipeline ships it. You catch it in production, roll back **through the pipeline**
(a revert PR, never by hand), then add a test so it can never ship again.

Keep a timeline as you go (copy the times from GitHub and the Actions logs).

| Event | Time |
|---|---|
| T0: bad PR merged | |
| T1: bad version live (verify log) | |
| T2: problem detected | |
| T3: revert PR merged | |
| T4: good version live again (verify log) | |
| **Merge → live** = T1 − T0 | |
| **Rollback → recovered** = T4 − T2 (also note T4 − T3) | |

---
## 1. Ship the bad release
```powershell
git checkout main ; git pull
git checkout -b refactor/decision-label
```
In `app/main.py`, change
```python
    decision = "reject" if prob >= model.THRESHOLD else "approve"
```
to (the bug)
```python
    decision = "approve" if prob >= model.THRESHOLD else "reject"
```
```powershell
git commit -am "refactor: simplify decision label"
git push -u origin refactor/decision-label
```
Open PR → `test` ✅ (the bug passes CI) → **Merge**. Note **T0**. Wait for `verify` ✅, and note **T1** plus the `MERGE TO LIVE` line.
📸 PR with green checks; verify log.

## 2. Detect it in production
```powershell
$URL = "https://<name>.onrender.com" ; $KEY = "<your key>"
curl.exe -s -X POST "$URL/api/v1/predictions" -H "X-API-Key: $KEY" -H "Content-Type: application/json" `
  -d '{\"income\":500,\"loan_amount\":20000,\"loan_term\":12,\"credit_score\":450,\"employment_years\":0}'
```
You'll see `default_probability` ≈ 0.99 with `"decision":"approve"`. That's wrong. Note **T2**. 📸

## 3. Roll back through the pipeline
GitHub → the merged PR → **Revert** button → creates a revert PR → `test` ✅ → **Merge** (note **T3**).
*(or: `git checkout main; git pull; git revert -m 1 <merge-sha>` on a new branch → PR)*
Wait for `verify` ✅ and note **T4**. Run the same curl again: now `"decision":"reject"`. 📸
`/health` now shows the revert commit's SHA. 📸

> Why not Render's "Rollback" button? It would be a deploy by hand. The revert goes through
> test → deploy → verify like every other release, and Git history shows exactly what happened.

## 4. Add the test that prevents it
```powershell
git checkout main ; git pull
git checkout -b test/decision-regression
copy drill\test_regression_decision.py tests\
pytest -q                                  # passes on the fixed code
```
**Prove the test catches the bug:** re-apply the bad line locally and run `pytest -q`. It must
FAIL (📸 the failure). Then undo: `git checkout app/main.py`.

Also make the pipeline's production check guard the rule: in `.github/workflows/ci-cd.yml`,
**verify → Production smoke test**, add at the end:
```yaml
          d=$(curl -s -X POST "$APP_URL/api/v1/predictions" -H "X-API-Key: $API_KEY" \
            -H 'Content-Type: application/json' \
            -d '{"income":500,"loan_amount":20000,"loan_term":12,"credit_score":450,"employment_years":0}' \
            | python3 -c 'import sys,json;print(json.load(sys.stdin)["decision"])')
          echo "risky applicant -> $d"; test "$d" = reject
```
```powershell
git add . ; git commit -m "test: pin approve/reject rule (regression from drill)" ; git push -u origin test/decision-regression
```
PR → ✅ → Merge.

## 5. What to write in the report
- Timeline table with both timings
- Root cause: tests checked the *shape* of `decision`, not its *meaning*
- Fix: revert through the pipeline (no hand deploy)
- Prevention: 3 regression tests + a production smoke check on a known-risky applicant
