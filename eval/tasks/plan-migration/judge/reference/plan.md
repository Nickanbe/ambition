# Plan: move the nightly cron batch to a job queue

## What the last 60 nights show (logs/nightly.log)

| Job | Finding | Evidence |
|---|---|---|
| export_orders.sh | **Fails silently ~10%.** sftp output is piped through `tee ... \|\| true` and the script ends `exit 0`, so the queue would mark it succeeded. | 6 of 60 nights log `ERROR sftp upload failed; orders file not delivered` followed by `END exit=0` |
| sync_inventory.py + rebuild_search_index.sh | **Overlap and contend on `products`.** sync takes a SHARE ROW EXCLUSIVE lock for its whole run (14-44 min); rebuild starts at 02:00 and needs ROW EXCLUSIVE. | lock waits on 33 of 60 nights; 7 deadlocks where sync was aborted and stock was not updated |
| aggregate_daily_sales.py | **Hard 06:00 deadline**: finance_report on bi-01 emails the CFO from daily_sales at 06:00. | median finish 04:57, p90 05:49; 12 nights after 05:30; 2 nights missed (09-14, 10-12, report sent with zeros). Runs ~168 min on overlap nights vs ~116 otherwise |
| apply_late_fees.py | **Not idempotent.** Adds the fee to balance_cents and inserts a ledger row with no run key. Any retry double-charges. | 09-30 manual re-run after a lost connection charged 51 accounts twice (INC-2291, 2 chargebacks) |
| cleanup_tmp.sh | Safe to retry. | |

The queue gives at-least-once delivery with automatic retries, so the two dangerous jobs (silent failure, non-idempotent) must be fixed **before** they move, not after.

## Design

- Queue: Postgres-backed (e.g. a `jobs` table with SKIP LOCKED, or pg-boss/Graphile Worker style). Same DB as the jobs, transactional enqueue, no new infra. Decision owner: platform lead, this week.
- A scheduler enqueues a nightly DAG instead of fixed clock times:
  `export_orders` and `sync_inventory -> rebuild_search_index` (serialized: one `products` writer at a time, via a concurrency key / advisory lock) and `aggregate_daily_sales` (high priority, does not wait on the search rebuild) then `apply_late_fees`, `cleanup_tmp`.
- Every job reports success only by exit code / thrown error; success also requires a postcondition check.

## Per-job changes before migration

1. **apply_late_fees**: add `run_date` and a unique constraint on `ledger (invoice_id, kind, run_date)`; insert ledger first with `ON CONFLICT DO NOTHING` and update the balance only for rows actually inserted, in one transaction. Test: run it twice for the same date in staging; balance and ledger counts unchanged on the second run. Owner: billing.
2. **export_orders**: `set -euo pipefail`, drop `|| true`, verify the remote file size after upload; non-zero exit on failure so the queue retries (upload is idempotent: same filename). Alert after 3 failed attempts. Owner: ops.
3. **sync_inventory / rebuild_search_index**: drop the table-wide lock (per-batch updates), run them under one concurrency key so they never overlap. Target: 0 deadlocks, 0 lock waits > 1 s.
4. **aggregate_daily_sales**: start as soon as export is done (~01:10) instead of 02:30, own priority lane, deadline alert at 05:15 if not done, page at 05:45. Target: finishes by 05:00 on 100% of nights (today 58/60 by 06:00).

## Cutover

Week 1: fix the four jobs on cron (fixes are useful regardless). Week 2: run the queue in shadow for cleanup_tmp and export_orders. Week 3: move the rest, keeping crontab lines commented for a one-command rollback. Late fees moves last, after the double-run test passes.

## Success criteria (checked from the queue's job table for 14 nights)

- Zero silent failures: every logged ERROR corresponds to a failed job.
- Zero duplicate late-fee ledger rows (`select invoice_id, run_date, count(*) ... having count(*) > 1` returns nothing).
- daily_sales ready before 06:00 on 14/14 nights, p90 before 05:00.
- No lock waits on `products` in the Postgres log.

## Risks

- Retries amplify any job we missed: audit each job for side effects before it moves.
- The BI box's 06:00 read is outside our control: ask BI for a readiness flag check so they never send zeros.
