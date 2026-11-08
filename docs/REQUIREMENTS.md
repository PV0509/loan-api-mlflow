# Requirements and evidence

| # | Requirement | How you prove it | Report section |
|---|---|---|---|
| 1 | CI green on `main`; branch rule requires `test` | Actions run screenshot; branch rule screenshot | 1 |
| 2 | Live API matches the Module 2 spec | `compare_spec.py` table + notes on deliberate changes | 1 |
| 3 | Model lifecycle tracked | MLflow runs (≥6, ≥2 model types), registry @champion/@challenger, promotion memo | 2 |
| 4 | Drift monitored with an alert plan | `monitor.png` + thresholds (warn 0.10 / alert 0.25) and actions | 2 |
| 5 | Change shipped by PR, deployed only by the pipeline | PR page, pipeline graph, verify log, live `/health` with new SHA, **merge→live time** | 3 |
| 6 | API secured; HTTPS | 3 API-key checks (health / 401 / list), SSL Labs grade | 4 |
| 7 | No secrets in repo, images or logs | `git grep` result, `.dockerignore`, masked `***` in Actions logs, keys only in GitHub/Render | 4 |
| 8 | Bad release caught and rolled back; test now prevents it | Drill timeline, **rollback→recovered time**, new test failing on the bad code | 5 |
| 9 | Presentation | 5-minute slides: architecture, decision, trade-off, next | 6 |
