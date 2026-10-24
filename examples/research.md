## Ambition: Explain newsletter open-rate drop from 41% to 33% [research] [full] 2026-10-16

### Baseline
Export per-send stats from the ESP dashboard, chart open rate against known changes (subject lines, send time, list growth, template), and write a one-page memo naming the likely cause.

### Passes

**Altitude**
1. Explain the 8-point drop and what to change before the next send. Needs: ESP exports, a dated log of changes since June.
2. Know whether readers are receiving and reading each issue, by mailbox provider and cohort (the number that matters if sponsorships are priced on opens). Needs: event-level data, Google Postmaster Tools, Microsoft SNDS, DMARC reports.
3. Own reader engagement continuously: after every send, split any change into measurement, list mix, deliverability and content, track a human-engagement metric instead of raw opens, and alert before a slide reaches 2 points. Needs: read-only ESP API, a scheduled job, an alert channel.

Stop there: "grow the newsletter" is past what this access can measure.

**Depth**
1. *Unasked:* check whether the ruler moved before the readers did. Since Apple Mail Privacy Protection, many opens are machine prefetches, and ESPs change how they filter machine and scanner opens. A filtering change, a shift in the Apple share, or a new denominator (sent vs delivered, suppression rules) can move the rate 8 points with no change in reading. Then check inbox placement by provider.
2. *Raw material:* per-recipient events for 26 weeks (every open and click with timestamp, IP and user agent; bounce and deferral codes; unsubscribes; complaints), the subscriber table, DMARC aggregate XML, Postmaster history, raw headers from a seed send. Not the dashboard percentage.
3. *Methods and tools:* DuckDB over the export; rule-based classification of opens and clicks (Apple proxy, scanner hits seconds after delivery, human); Kitagawa decomposition of the 8 points into list mix vs within-segment rate across provider x signup cohort x source; change-point detection (ruptures) to date each break against the change log; a fixed cohort present all 26 weeks; a seed-list placement test (GlockApps or similar).
4. *Outside judge:* human clicks per delivered, scanner clicks stripped; Postmaster Tools and seed placement; the ESP's written confirmation of any tracking or filtering change and its date; forecasts scored against the next three sends.

**Stretch target:** named causes summing to at least 7.6 of the 8 points (95%), each confirmed outside the analysis, plus a forecast of each of the next three sends' open rate within ±1 point, recorded before they go out.

**Assumption to challenge:** "Fewer people are reading." Rebuild the fixed cohort's rate from raw opens with machine opens removed. If human opens and clicks are flat, the drop is measurement or mix, and the 41% may have been the inflated number.

**New knowledge:** what share of this list's opens are human, by provider, and whether a composite of human opens, clicks and replies predicts 90-day retention better than raw opens. Fit on a random 80% of subscribers; test on the held-out 20% and the next four sends.

**Range**

Verbs: not "a memo on why opens fell" but "tell readers from machines, find who stopped receiving or reading and why, and decide what to change before the next send."

Subagents skipped: no raw material in reach yet.

| Field | Method | Artifact | Needs |
|---|---|---|---|
| Deliverability engineering | Authentication alignment, reputation history, bounce codes by provider, seed placement | Per-provider placement timeline | DNS, Postmaster, SNDS, DMARC reports, seed tool |
| Demography | Rate standardization, Kitagawa decomposition by cohort | Composition vs within-segment waterfall summing to -8 pts | Subscriber table with signup date, source, domain |
| Ad-fraud measurement | Classify machine opens and clicks by IP range, user agent, latency | Human-only open and click series per send | Event-level opens and clicks with IP, UA, timestamps |
| Survey research | One-question survey and short interviews of readers who went from clicking to silent | Reasons in readers' words, coded by frequency | OK to email a targeted segment |
| Forensic accounting (adversarial) | Restate six months under one metric definition; hunt definition breaks; test whether 41% was inflated | Restated series and dated list of breaks | ESP changelog, the export, figures quoted to sponsors |

### Upgrades (ranked)
| # | Type | Upgrade | Cost | Payoff | Judge |
|---|---|---|---|---|---|
| 1 | Depth | Restate the series from raw events: human vs machine opens, fixed cohort, per provider | ~1 hour of agent time; you supply the event export | Know whether readers left or the ruler moved | Human-click series; ESP's written confirmation of any filtering change |
| 2 | Depth | Decompose the 8 points into mix vs rate, date each break, forecast the next sends | Hours of agent time; subscriber table and change log; three weekly sends | Named causes covering at least 95% of the drop | Forecasts within ±1 pt on the next three sends |
| 3 | Depth | Deliverability audit plus seed-list placement test | ~1 hour of agent time; DNS, Postmaster, SNDS access; seed-tool subscription; one send | Learn whether Gmail or Outlook are sending you to spam | Seed placement results; Postmaster spam rate and reputation |
| 4 | Altitude | Post-send monitor: decomposition, human-engagement metric, alert at 2-point drift | ~1 day of agent time; API key, alert channel, 30 minutes to approve the metric; six sends | Catch the next slide in a week, not two months | Backtest alerts on this drop within two sends; then live over six |
| 5 | Range | Survey and interviews of readers who went silent | ~1 hour of agent time; your OK to send, 3-4 calls; two weeks elapsed | Causes in readers' own words | The respondents; reasons checked against #2 |

### Recommended brief
> Explain the newsletter's open-rate drop from 41% to 33% over the last eight weeks, covering at least 95% of the 8 points, each cause confirmed by a source outside this analysis. Work from raw data, not the dashboard: per-recipient events for 26 weeks, the subscriber table, a dated change log, DMARC reports, Postmaster and SNDS history.
>
> 1. Load everything into DuckDB. Classify every open and click as Apple proxy, scanner or human. Restate weekly open rate as human opens / delivered and say whether the 41% survives.
> 2. Compare a fixed cohort (present all 26 weeks) with the full list on human opens and clicks.
> 3. Kitagawa-decompose the change across provider x signup cohort x source into list mix and within-segment rate. Date each break with change-point detection and match it to the change log.
> 4. Audit deliverability: authentication alignment, reputation and spam rate, bounce codes by provider, one seed-list placement test.
> 5. Try to break the conclusion twice: argue it is a measurement artifact, then a deliverability problem. Keep what survives.
> 6. Deliver a waterfall of named causes with their outside confirmations, and a recorded forecast of the next three sends' open rate by segment within ±1 point.
>
> Do not change send settings, lists or DNS. List what you could not confirm and what would confirm it.

### Needs from you
- Per-recipient events for 26 weeks (opens and clicks with timestamp, IP, user agent; bounces; unsubscribes; complaints), or a read-only ESP API key.
- Subscriber table with signup date, source, mailbox domain.
- Dated changes since June: ESP notices, template, send time, sending domain or IP, list imports or cleanups.
- Read access to DNS, Postmaster Tools, SNDS, DMARC reports.
- Decision: seed-tool budget; OK to send one seed test and one survey.
- Whether open rate is quoted to sponsors.
- Whether the agent can run Python and DuckDB, and later schedule jobs.
