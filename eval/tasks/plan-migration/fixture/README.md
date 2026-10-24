# Nightly batch

Six cron jobs on db-batch-01 (see `crontab`, scripts in `jobs/`). `logs/nightly.log` is the combined log for the last 60 nights.

We want to move these to a job queue (workers pull jobs; failed jobs are retried automatically, at-least-once delivery). Queue tech is not chosen yet; candidates are a Postgres-backed queue or Redis + workers.
