# Ambition eval results, 2026-10-24

Method in SPEC.md. One run per arm per task (n=1), Opus 5.5, no network, light mode throughout. Auto scores come from each task's `judge/judge.py`; planning plans also await Nick's blind ranking (`runs/r1/blind/`, key in `blind-key.json`).

## Scores (B = the skill's Recommended brief, A = the task as asked)

| Task | A | B, skill as shipped (r1) | B, revised skill | Notes |
|---|---|---|---|---|
| feat-crash | 0.30 | 1.00 | 1.00 (r3) | A fixed one input; B hardened the class, fuzzed 10k files. r2 regressed to 0.30 (see below) |
| feat-export | 0.50 | 1.00 | not re-run | A missed spreadsheet formula injection |
| feat-perf | 1.00 | 1.00 | not re-run | both ~200-400x |
| feat-control | 1.00 | 0.16 | 0.95 (r3) | r1 turned a rename into a shim, snapshots and 7 new files |
| res-drop | 1.00 | 1.00 | not re-run | judge bug fixed (case-sensitive "India") |
| res-churn | 0.93 | 0.96 | not re-run | B: AUC 0.832, p@100 0.28 vs A 0.829, 0.22 |
| res-abtest | 1.00 | 0.00 | 1.00 (r2) | r1 brief dropped the answer.json schema |
| res-control | 1.00 | 1.00 | 1.00 (r2) | r1 added an extra notes file the judge tolerated |
| plan-ci | 1.00 | 0.86 | not re-run | B built a replay model accurate to ~6 s/run; judge's "uses the data's numbers" check missed B's derived numbers (judge false negative, left as is) |
| plan-launch | 1.00 | 1.00 | not re-run | auto judge saturated; blind rank pending |
| plan-migration | 1.00 | 1.00 | not re-run | auto judge saturated; blind rank pending |
| plan-control | 1.00 | 1.00 | 1.00 (r2) | |

Revised skill: B wins 3 (crash, export, churn), ties 7, loses 2 by small margins (control -0.05 for one README line it fixed; plan-ci -0.14, judge artifact). Stretch target was 10 of 12 wins: **missed**. Main reason: plain Opus already reads the raw data and finds the planted facts on 7 of 12 tasks, so those auto judges sit at 1.0 for both arms.

## What the eval showed

1. **Where the skill pays: feature work with a class of failure behind the request.** The crash and export briefs turned "fix this one input" into "harden the class" and won by 0.5-0.7.
2. **Analysis and planning: the baseline is already deep.** A found the planted tracking bug, SRM, price cohort and CI causes unprompted. B's extra (replay models, per-customer schedules, honest misses against stretch targets) is real but beyond what these judges score; blind ranking will say whether it is worth 2-3x the length.
3. **Brief must stand alone.** r1 res-abtest brief said "in the requested schema" without the schema; the executor never saw the original task. Fixed.
4. **Invoked-by-name trivial tasks got inflated.** Fixed, then over-fixed: r2 classed the crash fix as trivial ("change nothing else"). Final rule: trivial means the pass finds nothing worth adopting, not that the task is small.
5. **Light mode ran 386-603 words in r1** against "about 400". With the 450 cap, r2/r3 ran 404-458.
6. **Cost of B:** roughly 2-4x A's wall time on non-trivial tasks (e.g. feat-perf 57 s vs 13 min; res-churn 2.4 vs 9 min).

## Not yet done

- Re-run the 7 tasks the revisions did not target, on the final SKILL.md (expect ties; confirms no other regression).
- Repeats (n=3) to separate signal from run-to-run noise.
- Harder tasks where plain Opus does not saturate the judge (e.g. planted facts that need a cross-file join or a held-out test the prompt doesn't hint at).
- Nick's blind ranking of the three planning pairs.
