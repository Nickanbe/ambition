# Rubric: plan-launch

Rank the plans X and Y (blind; arm labels shuffled). Score each criterion 1-5, then give an overall preference.

1. **Grounded in the data.** Does it use what is actually in the working directory (customers.csv, pricing.md, support_tickets.csv, notes/price_change_2024.md, notes/terms_excerpt.md), with numbers pulled from it, rather than advice that fits any team?
2. **Decisions clear.** Is it obvious what will be done, in what order, and what was decided against? Are the open decisions named with who makes them?
3. **Measurable success criteria.** Is there a target and a way to check it later from real data (not "faster", "lower churn")?
4. **Risks and owners.** Are the risks specific to this situation, with mitigations, and does each piece of work have an owner?
5. **Would you actually run it?** If this landed on your desk, would you execute it as written, or would you have to redo the analysis first?

Things a strong plan should notice here (for the ranker; also what judge.py checks automatically):
- 299 annual Pro customers are on price-locked contracts (terms 8.1, `price_locked_until`): they keep $20 until renewal.
- EU customers (396 Pro, 304 monthly) require at least 30 days' notice and a free cancel right (terms 8.2); 2024 gave only 14 days.
- 197 Pro customers are heavy-usage, single seat, no integrations: Starter ($12) covers everything they use, and tickets say they would downgrade.
- In 2024 the churn spike was concentrated in customers in their first 0-1 months (18.5% vs 6.0% baseline; ~70% of excess churn).
