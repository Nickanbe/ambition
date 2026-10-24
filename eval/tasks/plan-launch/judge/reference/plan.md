# Launch plan: Pro $20 -> $25

## Who this touches (customers.csv, 2026-10-01)

| Segment | Pro customers | Treatment |
|---|---|---|
| All Pro | 1,511 | |
| Annual, price-locked contracts | 299 | **Grandfathered** until `contract_end` (terms 8.1: fixed for the term). New price at renewal; renewal dates spread 2026-10 to 2027-10, so the uplift phases in over 12 months |
| Monthly | 1,212 | New price, per schedule below |
| ... of which EU | 304 monthly (396 Pro total) | **30 days' notice** and a cancel-without-charge right (terms 8.2), not the 14 days used in 2024 |
| ... of which tenure 0-1 months | 190 | Protected (see below) |
| Heavy-usage, single seat, no integrations | 197 (155 monthly) | Downgrade risk to Starter $12 |

Upside if nobody leaves: 1,212 x $5 = $6,060 MRR now, plus $50/yr per annual contract as it renews.

## What 2024 taught us

The $15 -> $20 change spiked churn from 2.4% to 4.1% for one month, and customers in their first 0-1 months churned at 18.5% (vs 6.0% baseline). ~70% of the excess churn was new customers who had just signed up at the old price, with 14 days' notice. Downgrades to Starter were never tracked.

So:
1. **Protect new customers:** anyone with tenure under 3 months on the announce date keeps $20 until their 3-month anniversary. Costs ~$950/mo for up to 3 months; aims to avoid the 18.5% spike.
2. **Track downgrades separately** from churn this time.

## The heavy single-seat segment

197 Pro customers use one seat and zero integrations but run 38k-120k events a month; 8 recent tickets say they would move to Starter if Pro goes up. At $25 they would save $13/mo by downgrading. If all 155 monthly ones downgrade we lose 155 x $8 = $1,240 MRR vs today, ~20% of the upside.
Decision for product (owner: PM, before announce): either (a) add a usage-based Starter limit (e.g. 25k events) so Starter is not a substitute for heavy users, or (b) offer this segment a 12-month $20 lock in exchange for annual billing. Recommend (b) for launch, (a) as a separate decision.

## Timeline

- T-35: segment lists frozen; CS briefed; FAQ and macros ready.
- T-30: email + in-app notice to EU monthly customers (30 days, cancel right stated).
- T-21: email + in-app notice to all other monthly customers (more than the 14-day minimum).
- T-0: pricing page and new signups at $25; monthly invoices at $25 on next billing date.
- Annual: renewal reminder 30 days before each `contract_end` with the new price.

## Owners

Billing config + grandfather flags: billing eng. Notices: lifecycle marketing. Terms check (EU wording, annual): legal. Ticket macros: support lead. Dashboard: growth analyst.

## Success criteria (reviewed at day 30 and day 90)

- Pro logo churn month 1 <= 3.0% (2024: 4.1%), and churn for tenure 0-3 months not above its 6.0% baseline.
- Downgrades to Starter from the heavy single-seat segment < 15% (<= 30 of 197).
- Net Pro MRR +$4,500 or more at day 90.
- Zero EU or annual-contract customers billed at $25 early (audit query on invoices).

## Risks

- Annual-lock flags missing on some contracts: verify `price_locked_until` against order forms for the 299 before T-30.
- Support volume spike at T-21: staff +1 CS for two weeks.
- Rollback: if month-1 churn > 5%, extend $20 for tenure < 6 months and pause the next notice wave.
