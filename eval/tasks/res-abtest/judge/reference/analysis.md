# res-abtest reference analysis

Naive read: A 34.21% (n=64,901), B 35.55% (n=55,618), +3.9% relative, z ~ 4.9. Looks like a clear win.

It is not real. The split was meant to be 50/50 and is 54/46 (chi-square 715, p << 0.001): a sample ratio mismatch. Breaking counts down by platform and app version, iOS app 8.4 has 9,673 A users and 0 B users; every other cell splits evenly. B users on iOS 8.4 were never logged. That segment converts below average (26% vs 34% overall), so dropping it from B only shifts B's mix toward desktop and inflates its conversion.

On the properly assigned population (iOS 8.4 excluded from both arms; split 55,228 / 55,618, chi-square 1.4) the lift is +0.3% (95% CI -1.3% to +1.8%). Desktop +0.2%, mobile -0.2%. Do not ship on this evidence: fix the iOS 8.4 assignment logging and rerun, since B has never been observed for those users at all.

`analysis.py` reproduces `answer.json` from the fixture.
