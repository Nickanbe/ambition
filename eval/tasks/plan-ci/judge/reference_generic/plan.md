# Plan to speed up CI

Our CI currently takes 38 minutes, which slows down developers. Here is a plan to bring it down.

## Goals
- Reduce CI time significantly, ideally under 15 minutes.
- Keep reliability high.

## Steps

1. **Profile the pipeline.** Look at which jobs take the longest and focus on those.
2. **Use caching.** Cache dependencies and build outputs between runs using GitHub Actions cache.
3. **Parallelize tests.** Split the test suite across more runners so tests finish faster.
4. **Optimize Docker builds.** Use multi-stage builds and layer caching to make image builds faster.
5. **Fix flaky tests.** Identify flaky tests and fix or quarantine them so we don't waste time on retries.
6. **Use faster runners.** Consider larger GitHub-hosted runners or self-hosted runners.
7. **Run only what changed.** Use path filters to skip jobs that are not affected by a change.

## Risks
- Caching can cause stale builds if keys are wrong.
- Parallelization can expose test isolation issues.

## Success criteria
- CI time under 15 minutes.
- Developers report faster feedback.
