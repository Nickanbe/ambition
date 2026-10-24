## Ambition: Add CSV export to the orders table [feature] [light] 2026-10-16

### Baseline
Add an "Export CSV" button that turns the rows already loaded in the orders table into a CSV in the browser and downloads it.

### Passes
- **Altitude:** The CSV is someone's guess at an outcome. Find where the file goes next (bookkeeping, a 3PL, refunds) and own that handoff, so nobody has to export at all.
- **Depth:** Stream every row that matches the current filters from Postgres on the server, with a fixed column contract and formula-injection escaping. Stretch target: 1M orders with flat memory and first byte under 300 ms.
- **Range:** As a verb, the export is "get order data to where the next decision is made, without leaking it." Crew: an accountant (columns that tie to payouts), a data engineer (streaming and the column contract), a pen tester (who can pull customer PII, CSV injection).

### Upgrades (ranked)
| # | Type | Upgrade | Cost | Payoff | Judge |
|---|---|---|---|---|---|
| 1 | Depth | Server-streamed export of all filtered rows, fixed columns, injection-escaped | ~1-2 h agent; column list from ops; seeded DB | Right file at any size, opens cleanly in Excel | Round-trip test against the DB on a hostile fixture; 1M-row load test |
| 2 | Range | Role-gate the export, drop unneeded PII, write an audit row per export | ~1 h agent; a decision on roles and PII | Customer data cannot leave silently | Tests: a disallowed role gets 403; each export writes an audit row |
| 3 | Altitude | Replace the recurring export with scheduled delivery to its real destination | Hours of agent work; 15 min with the ops lead; two weeks elapsed | The manual step disappears | Audit log shows manual exports falling to zero over two weeks while totals still tie to payouts |

### Recommended brief
> Add CSV export to the orders admin. In a server route, stream every order that matches the table's current filters from Postgres (cursor or COPY, never buffered in full). Use a fixed, documented column list, RFC 4180 quoting, a `'` prefix on cells starting with `=`, `+`, `-`, `@`, a tab or a CR, UTF-8 with a BOM, money as decimal strings and timestamps in ISO 8601 UTC. Allow only [roles], leave out [PII columns], and insert an `order_exports` row (user, filters, row count, time) for every export. Prove it with a round-trip test on a hostile fixture (formulas, commas, quotes, emoji), authz and audit integration tests, and a 1M-row seeded load test that reports first-byte time and peak memory.

### Needs from you
- Access to the repo and to a seeded or staging Postgres, and whether the agent can run tests there (all unknown).
- The columns ops needs, and where the file goes after it downloads.
- Which roles may export and which fields count as PII.
- The host's response-time limit (a serverless timeout caps how long a stream can run).
