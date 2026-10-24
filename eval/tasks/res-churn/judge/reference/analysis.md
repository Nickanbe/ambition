# res-churn reference analysis

`analysis.py` builds monthly snapshots (features as of the start of each month Apr-Sep 2026, label = canceled that month; ~600 historical cancellations), fits a logistic regression by IRLS, backtests on September (AUC 0.855 trained on Apr-Aug), refits on all months and scores the 2,398 accounts active on 2026-10-01.

Features that carry the signal (fitted weights): annual contract not renewing in the target month (-4.0, the strongest: those accounts cannot cancel), usage decline over the last 4 vs prior 8 weeks (-1.2 per log-unit of decline), sessions per seat (-0.9), billing tickets in the last 28 days (+1.0 each), admin gone quiet for 3 weeks after being active (+0.8). Raw activity level and seat count add almost nothing.

Holdout: AUC 0.844, precision@100 0.21 (base rate 4.1%). Oracle with the true simulated hazard: AUC 0.892, precision@100 0.36. Naive "lowest sessions in the last 4 weeks": AUC 0.603.
