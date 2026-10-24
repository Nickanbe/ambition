# Rubric: plan-migration

Rank the plans X and Y (blind; arm labels shuffled). Score each criterion 1-5, then give an overall preference.

1. **Grounded in the data.** Does it use what is actually in the working directory (crontab, the 6 scripts in jobs/, logs/nightly.log for 60 nights), with numbers pulled from it, rather than advice that fits any team?
2. **Decisions clear.** Is it obvious what will be done, in what order, and what was decided against? Are the open decisions named with who makes them?
3. **Measurable success criteria.** Is there a target and a way to check it later from real data (not "faster", "lower churn")?
4. **Risks and owners.** Are the risks specific to this situation, with mitigations, and does each piece of work have an owner?
5. **Would you actually run it?** If this landed on your desk, would you execute it as written, or would you have to redo the analysis first?

Things a strong plan should notice here (for the ranker; also what judge.py checks automatically):
- sync_inventory and rebuild_search_index overlap (lock waits on 33 of 60 nights, 7 deadlocks) and contend on the `products` table; they need serializing or the lock removed.
- export_orders fails silently on ~10% of nights (6 of 60): sftp error in the log, but `|| true` / `exit 0` means a queue would record success.
- apply_late_fees is not idempotent (adds the fee and inserts a ledger row with no run key); a queue retry double-charges, as the 09-30 manual re-run did (INC-2291, 51 accounts).
- aggregate_daily_sales has a hard 06:00 deadline (finance_report reads daily_sales); it missed twice and finished after 05:30 on 12 nights.
