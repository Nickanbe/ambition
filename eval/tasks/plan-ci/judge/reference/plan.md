# Plan: cut CI from 38 min to under 15 min

## Where the 38 minutes actually go (from ci_runs.csv, 200 attempts / 174 commits)

The workflow is a strict chain: install -> build-image -> unit (4 shards) -> e2e. Mean wall time is 37.7 min (p90 39.4 min).

| Stage | Mean | Finding |
|---|---|---|
| install (`npm ci`) | 6.1 min | `deps_cache_hit` is false on all 200 rows; setup-node has no `cache: npm` and there is no actions/cache keyed on package-lock |
| build-image | 7.0 min | `docker build --no-cache` on every run, but `dockerfile_sha` changed only twice in 200 runs (3 distinct values) |
| unit shards 1/2/4 | 4.0 / 4.2 / 3.9 min | fine |
| unit shard 3 | 12.1 min | about 3x the others: shards.json puts all of tests/integration in shard 3 alone, so the matrix waits on it |
| e2e | 11.5 min | Playwright runs with `--workers=1` and `fullyParallel: false`: 214 specs in serial |

Reruns: 26 of 174 commits (14.9%) failed once on the flaky `payment.spec.ts > applies coupon after price refresh` (timeout waiting for `/api/cart/reprice`, 5.3 s vs a 5 s expect timeout) and were re-run in full. Those commits cost ~76 min, so the effective mean per commit is 43.3 min, not 37.7.

## Target and how we measure it

- Target: p50 wall time per commit (including reruns) under 15 min, p90 under 18 min, within 3 weeks. Stretch: 10 min p50.
- Measure: re-export ci_runs.csv weekly (same columns) and compute per-commit wall time including reruns, rerun rate and per-stage means. Gate: the weekly number goes in the eng channel; a stage regressing >20% opens an issue.

## Changes, in order of minutes saved per hour of work

1. **Fix the flaky test (owner: checkout team, 1 day).** Wait on the reprice response instead of a fixed 5 s expect; quarantine it in a non-blocking job until fixed. Saves ~5.6 min effective per commit (15% x 37.7) and stops whole-workflow reruns. Success: rerun rate < 2% over the next 100 commits.
2. **Rebalance unit shards (owner: platform, half day).** Replace the static directory list with Jest/`--shard` by timing (or split tests/integration across 2 shards, 6 shards total). Critical path drops from 12.1 to ~5.5 min; saves ~6.5 min. Success: max/min shard ratio < 1.3.
3. **Cache dependencies (owner: platform, 1 hour).** `actions/setup-node` with `cache: npm` plus actions/cache on node_modules keyed by the package-lock hash; drop the upload/download artifact. Expected install 6.1 min -> ~1 min on hit. Success: cache hit rate > 90% in the CSV.
4. **Stop rebuilding an unchanged image (owner: platform, half day).** Remove `--no-cache`, use buildx with GHA cache, and tag by dockerfile_sha + lockfile hash; skip the build when the tag exists. Saves ~6 min on ~99% of runs. Run unit in parallel with build-image (unit does not need the image).
5. **Parallelize e2e (owner: QA, 2 days).** `fullyParallel: true`, 4 workers, then shard across 2 runners; fix the specs that share state (expect checkout/ first). 11.5 -> ~3.5 min.

Projected critical path: install 1 + max(image skip 0.5, unit 5.5) + e2e 3.5 ≈ 10-11 min, with reruns near zero.

## Risks

- Parallel e2e exposes shared-state specs: roll out per directory, keep `--workers=1` fallback flag for one week.
- Cache poisoning / stale node_modules: key strictly on lockfile hash + node version.
- Skipping the image build could ship stale images if the app code is COPY'd in: the tag must include the source hash for e2e images; only the base/deps layer is reused.

## Decision needed

Approve 2 extra runners for e2e sharding (cost) or accept ~6 min e2e with 4 workers on one runner.
