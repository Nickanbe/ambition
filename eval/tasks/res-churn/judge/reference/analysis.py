"""Reference churn model for res-churn (stdlib only).

    python3 -I analysis.py <fixture_dir> [out_dir]

Method (what a churn analyst would do):
  1. Build monthly snapshots: features as of the last week before month M, label =
     canceled in month M. Months Apr..Sep 2026 give ~580 historical cancellations.
  2. Features: usage trend (last 4 wk vs prior 8 wk, per account), sessions per
     seat, admin (champion) gone quiet, billing tickets in the last 4 weeks,
     annual contract not up for renewal in month M, log seats.
  3. Logistic regression (Newton/IRLS); backtest on Sep (trained Apr..Aug),
     then refit on all months and score October for the accounts still active.
"""
import csv, collections, datetime as dt, json, math, os, sys

fx = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "."
rd = lambda n: list(csv.DictReader(open(os.path.join(fx, n))))
acc = {a["account_id"]: a for a in rd("accounts.csv")}
users = rd("users.csv")
admin = {u["user_id"]: u["account_id"] for u in users if u["role"] == "admin"}
n_users = collections.Counter(u["account_id"] for u in users)
weeks = sorted({r["week_start"] for r in rd("weekly_activity.csv")})
widx = {w: i for i, w in enumerate(weeks)}
sess = collections.defaultdict(lambda: [0] * len(weeks))
adm = collections.defaultdict(lambda: [0] * len(weeks))
for r in rd("weekly_activity.csv"):
    i = widx[r["week_start"]]
    sess[r["account_id"]][i] += int(r["sessions"])
    if r["user_id"] in admin:
        adm[r["account_id"]][i] += int(r["sessions"])
bill = collections.defaultdict(list)
for t in rd("support_tickets.csv"):
    if t["category"] == "billing":
        bill[t["account_id"]].append(t["created_at"])


def feats(a, m):
    """Features for account a as of the start of month m (2026)."""
    start = dt.date(2026, m, 1)
    cut = [i for i, w in enumerate(weeks) if dt.date.fromisoformat(w) + dt.timedelta(days=6) < start]
    if len(cut) < 4:
        return None
    e = cut[-1] + 1
    s = sess[a]
    last4 = sum(s[max(0, e - 4):e]) / 4
    prev = s[max(0, e - 12):e - 4]
    prev8 = sum(prev) / max(1, len(prev))
    trend = math.log((last4 + 1) / (prev8 + 1))
    seats = int(acc[a]["seats"])
    per_seat = math.log(1 + last4 / seats)
    ad = adm[a]
    admin_quiet = 1.0 if sum(ad[max(0, e - 3):e]) == 0 and sum(ad[:max(0, e - 3)]) > 0 else 0.0
    lo = str(start - dt.timedelta(days=28))
    bt = sum(1 for d in bill[a] if lo <= d < str(start))
    renew_m = int(acc[a]["signup_date"][5:7])
    locked = 1.0 if acc[a]["contract"] == "annual" and renew_m != m else 0.0
    return [1.0, min(0.0, trend), max(0.0, trend), per_seat, admin_quiet, min(bt, 3), locked, math.log(seats)]


def alive_at(a, m):
    c = acc[a]["canceled_at"]
    return (not c) or c >= "2026-%02d-01" % m


rows = []
for m in range(4, 10):
    for a in acc:
        if not alive_at(a, m):
            continue
        x = feats(a, m)
        if x is None:
            continue
        y = 1 if acc[a]["canceled_at"][:7] == "2026-%02d" % m else 0
        rows.append((m, x, y))


def fit(data, it=25, l2=1e-2):
    """Logistic regression by Newton-Raphson (IRLS) with a small ridge."""
    k = len(data[0][1])
    w = [0.0] * k
    for _ in range(it):
        g = [0.0] * k
        H = [[0.0] * k for _ in range(k)]
        for _, x, y in data:
            z = sum(wi * xi for wi, xi in zip(w, x))
            p = 1 / (1 + math.exp(-max(-30, min(30, z))))
            q = p * (1 - p)
            for i in range(k):
                g[i] += (p - y) * x[i]
                for j in range(k):
                    H[i][j] += q * x[i] * x[j]
        for i in range(k):
            g[i] += l2 * w[i]
            H[i][i] += l2
        # solve H d = g (Gaussian elimination)
        M = [H[i][:] + [g[i]] for i in range(k)]
        for c in range(k):
            piv = max(range(c, k), key=lambda r: abs(M[r][c]))
            M[c], M[piv] = M[piv], M[c]
            for r in range(k):
                if r != c and M[c][c]:
                    f = M[r][c] / M[c][c]
                    M[r] = [a - f * b for a, b in zip(M[r], M[c])]
        d = [M[i][k] / M[i][i] for i in range(k)]
        w = [wi - di for wi, di in zip(w, d)]
    return w


def auc(sc, lab):
    pr = sorted(zip(sc, lab))
    pos = sum(lab); neg = len(lab) - pos
    r = 0; rank_sum = 0
    for i, (_, l) in enumerate(pr):
        if l:
            rank_sum += i + 1
    return (rank_sum - pos * (pos + 1) / 2) / (pos * neg)


score = lambda w, x: 1 / (1 + math.exp(-sum(wi * xi for wi, xi in zip(w, x))))
wb = fit([r for r in rows if r[0] < 9])
bt = [r for r in rows if r[0] == 9]
print("backtest Sep AUC:", round(auc([score(wb, x) for _, x, _ in bt], [y for _, _, y in bt]), 3))
w = fit(rows)
print("weights:", [round(v, 2) for v in w])
active = [a for a in acc if not acc[a]["canceled_at"]]
pred = sorted(((score(w, feats(a, 10)), a) for a in active), reverse=True)
ans = {"ranking": [{"account_id": a, "score": round(p, 4)} for p, a in pred]}
json.dump(ans, open(os.path.join(out, "answer.json"), "w"))
print("wrote", len(pred), "accounts")
