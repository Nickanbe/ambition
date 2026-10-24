# Data

Covers 2025-01-01 to 2025-03-31 and 2026-01-01 to 2026-03-31.

## signups.csv
One row per signup event recorded by the product analytics pipeline.

| column | meaning |
|---|---|
| event_time | UTC timestamp of the signup event |
| user_id | user who signed up |
| browser, browser_version | browser reported by the client |
| country | ISO country code |
| channel | acquisition channel |
| plan | plan chosen at signup (free, pro, team) |
| price_shown_usd | monthly pro price shown on the pricing page, USD |

## billing_accounts.csv
One row per account created in the billing system.

| column | meaning |
|---|---|
| account_id | billing account |
| user_id | user who owns the account |
| created_at | UTC timestamp the account was created |
| country | ISO country code |
| plan | plan at creation |
| monthly_price_usd | monthly price billed, USD (0 for free) |
