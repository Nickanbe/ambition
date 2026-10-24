# Data

Checkout A/B test, 2026-09-01 to 2026-09-28. A = current checkout, B = new checkout. Users were meant to be split 50/50 when they reached checkout.

## assignments.csv
One row per user in the experiment.

| column | meaning |
|---|---|
| user_id | user |
| variant | A or B |
| assigned_at | UTC timestamp of assignment |
| device | desktop or mobile |
| platform | web, ios_app or android_app |
| app_version | app version (blank for web) |
| country | ISO country code |

## orders.csv
One row per order placed by an experiment user after assignment.

| column | meaning |
|---|---|
| order_id | order |
| user_id | user who ordered |
| ordered_at | UTC timestamp |
| order_value_usd | order value, USD |
