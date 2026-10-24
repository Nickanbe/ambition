# Plan: migrate nightly cron jobs to a job queue

## Why
Cron jobs are hard to monitor, don't retry on failure, and run on a single box. A job queue gives us retries, visibility, and horizontal scaling.

## Steps
1. **Choose a queue.** Evaluate Sidekiq, Celery, BullMQ, or a Postgres-backed queue. Pick based on team familiarity and existing infrastructure.
2. **Inventory the jobs.** List every cron entry, its schedule, owner and dependencies.
3. **Wrap each script as a job.** Convert each script into a job handler that the worker can run.
4. **Add a scheduler.** Use the queue's scheduler to enqueue jobs at the same times as the crontab.
5. **Make jobs idempotent.** Jobs may be retried, so make sure running them twice is safe.
6. **Add monitoring and alerting.** Track failures, durations and queue depth in a dashboard; alert on failures.
7. **Migrate gradually.** Move one job at a time, run in parallel with cron for a week, then disable the cron entry.
8. **Document** the new setup and runbooks.

## Risks
- Duplicate execution during the parallel-run period.
- Learning curve for the new tool.

## Success criteria
- All jobs running from the queue with no missed runs for two weeks.
- Failures are visible and alerted.
