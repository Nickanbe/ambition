# res-drop reference analysis

Observed daily signup events: Feb 2026 403.6/day -> Mar 2026 327.5/day (-18.9%). Billing accounts fell only 7.8%.

1. **Tracking loss, ~59% of the drop.** 1,389 billing accounts created from 2026-03-03 have no signup event. Safari 19.3 drops from ~13% of events to zero on that date while every other browser is steady. The signups happened; analytics lost them.
2. **IN price increase, ~30%.** Pro price shown in IN went from $8 to $12 on 2026-03-01. Real IN signups (billing) fell ~32% against the trend in other countries.
3. **Noise, ~11%.** A small dip across all segments.

Not a cause: paid_social is down ~45% MoM, but it fell 33% Feb->Mar 2025 as well (March budget pause, offset by organic_search), and total signups were flat Feb->Mar 2025. The extra 2026 decline in that channel is the two causes above flowing through it.

`analysis.py` reproduces `answer.json` from the fixture.
