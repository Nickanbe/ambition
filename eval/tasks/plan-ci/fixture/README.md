# acme-app CI

Files here:
- `.github/workflows/ci.yml`: the pipeline
- `ci_runs.csv`: the last 200 workflow runs (one row per run attempt), per-job durations in seconds
- `flaky-tests.log`: e2e failures that were followed by a manual re-run
- `tests/shards.json`, `playwright.config.ts`, `Dockerfile`: config the pipeline uses

Developers say "CI takes 38 minutes".
