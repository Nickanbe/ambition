# Data

Activity runs from the week of 2026-03-02 through the week of 2026-09-21. Today is 2026-10-01.

## accounts.csv
| column | meaning |
|---|---|
| account_id | account |
| plan | starter, pro or enterprise |
| seats | seats purchased |
| mrr_usd | monthly recurring revenue, USD |
| contract | monthly or annual |
| next_renewal_date | next renewal date (blank for canceled accounts) |
| signup_date | date the account was created |
| region, industry | firmographics |
| canceled_at | date the account canceled (blank if still a customer) |

## users.csv
| column | meaning |
|---|---|
| user_id | user |
| account_id | account the user belongs to |
| role | admin or member |
| created_at | date the user was added |

## weekly_activity.csv
One row per user per week with at least one session.

| column | meaning |
|---|---|
| week_start | Monday of the week |
| user_id, account_id | who |
| sessions | sessions that week |
| key_actions | core product actions that week |

## support_tickets.csv
| column | meaning |
|---|---|
| ticket_id | ticket |
| account_id | account that filed it |
| created_at | date filed |
| category | billing, bug, how_to or feature_request |
| priority | low, normal or high |
