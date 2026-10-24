# Rubric: plan-ci

Rank the plans X and Y (blind; arm labels shuffled). Score each criterion 1-5, then give an overall preference.

1. **Grounded in the data.** Does it use what is actually in the working directory (ci.yml, ci_runs.csv with 200 runs, flaky-tests.log, shards.json, playwright.config.ts, Dockerfile), with numbers pulled from it, rather than advice that fits any team?
2. **Decisions clear.** Is it obvious what will be done, in what order, and what was decided against? Are the open decisions named with who makes them?
3. **Measurable success criteria.** Is there a target and a way to check it later from real data (not "faster", "lower churn")?
4. **Risks and owners.** Are the risks specific to this situation, with mitigations, and does each piece of work have an owner?
5. **Would you actually run it?** If this landed on your desk, would you execute it as written, or would you have to redo the analysis first?

Things a strong plan should notice here (for the ranker; also what judge.py checks automatically):
- Unit shard 3 (all of tests/integration) averages 12.1 min vs ~4 min for the other shards (about 3x), so the matrix waits on it.
- `npm ci` takes ~6.1 min and `deps_cache_hit` is false on every run (no setup-node cache, no actions/cache).
- The flaky `payment.spec.ts > applies coupon after price refresh` forced full re-runs on 26 of 174 commits (~15%); those commits take ~2x, so effective time is ~43 min, not 38.
- `docker build --no-cache` costs ~7 min every run, although `dockerfile_sha` changed only twice in 200 runs.
- e2e (~11.5 min) runs with `--workers=1` and `fullyParallel: false`.
- A target (e.g. p50 < 15 min) with a way to measure it from the run data.
