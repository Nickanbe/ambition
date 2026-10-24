"""Seeded generator for res-churn. Writes fixture/*.csv, judge/labels.csv, judge/truth.json.

Simulation (weekly, 2026-03-02 .. 2026-09-27; holdout = cancellations in October 2026):
  * Each account has latent health h (mean-reverting random walk) plus occasional
    decline episodes (h falls for 4-10 weeks).
  * Weekly sessions per user ~ Poisson(lam_user * exp(0.8 h)). Volume is driven
    mostly by seat count, so "lowest activity" is a weak signal by itself.
  * The admin (champion) can leave: their sessions go to zero.
  * Billing tickets are more likely when h is low; bug/how_to tickets are noise.
  * Monthly churn hazard (decided at the start of each month):
        logit = -4.3 - 1.5 h + 2.6 * max(0, -(h - h_6wk_ago)) + 2.2 champion_gone
                + 1.0 * billing_tickets_last_4wk
    Annual contracts can only cancel in their renewal month (otherwise x0.03).
Planted signal an expert finds: usage trend (not level), per-seat utilisation,
champion loss, billing tickets, and the contract renewal calendar. Historical
cancellations (Apr-Sep) are in the fixture so a model can be backtested.

Run: python3 -I judge/generate.py   (from the task directory)
"""
import csv
import datetime as dt
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
FIX = os.path.join(TASK, "fixture")
rng = random.Random(4242)

N_ACC = 3000
W0 = dt.date(2026, 3, 2)
NW = 30  # weeks starting 2026-03-02 .. 2026-09-21
WEEKS = [W0 + dt.timedelta(weeks=i) for i in range(NW)]


def pois(lam):
    if lam > 30:
        return max(0, int(round(rng.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def sig(x):
    return 1 / (1 + math.exp(-x))


def auc(scores, labels):
    pairs = sorted(zip(scores, labels), key=lambda t: t[0])
    # rank-based with ties averaged
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    npos = sum(l for _, l in pairs)
    nneg = len(pairs) - npos
    rs = sum(r for r, (_, l) in zip(ranks, pairs) if l)
    return (rs - npos * (npos + 1) / 2) / (npos * nneg)


def main():
    accounts, users, activity, tickets = [], [], [], []
    labels = {}
    oracle = {}
    uid = 0
    tid = 0
    for a in range(N_ACC):
        acc_id = "A%05d" % (10000 + a)
        seats = max(1, min(80, int(round(math.exp(rng.gauss(1.8, 0.8))))))
        plan = "enterprise" if seats >= 25 else ("pro" if seats >= 6 else "starter")
        annual = rng.random() < (0.65 if plan == "enterprise" else 0.35)
        signup = dt.date(2023, 1, 1) + dt.timedelta(days=rng.randrange(0, 1150))
        renewal_month = signup.month
        region = rng.choice(["NA", "NA", "EU", "EU", "APAC", "LATAM"])
        industry = rng.choice(["software", "agency", "retail", "healthcare", "finance", "education", "manufacturing"])
        mrr = seats * {"starter": 12, "pro": 25, "enterprise": 40}[plan]
        util = min(1.0, max(0.15, rng.betavariate(4, 2)))
        n_users = max(1, int(round(seats * util)))
        h = rng.gauss(0, 0.7)
        hist = []
        decline_left, decline_rate = 0, 0.0
        champ_gone = False
        u_list = []
        for k in range(n_users):
            uid += 1
            role = "admin" if k == 0 else "member"
            lam = rng.gammavariate(3.0, (2.5 if role == "member" else 6.0) / 3.0)
            u_list.append(("U%06d" % uid, role, lam, rng.random() < 0.08))  # some members dormant
            users.append({"user_id": "U%06d" % uid, "account_id": acc_id, "role": role,
                          "created_at": str(signup + dt.timedelta(days=rng.randrange(0, 60)))})
        canceled_at = None
        billing_weeks = []
        month_seen = set()
        for w, wk in enumerate(WEEKS + [dt.date(2026, 10, 5)]):
            # month-start churn decision (first week whose start is in a new month Apr..Oct)
            if wk.month not in month_seen and w > 0:
                month_seen.add(wk.month)
                h6 = hist[-6] if len(hist) >= 6 else hist[0]
                bt = sum(1 for bw in billing_weeks if bw >= w - 4)
                z = -4.3 - 1.5 * h + 2.6 * max(0.0, -(h - h6)) + 2.2 * champ_gone + 1.0 * bt
                p = sig(z)
                if annual and wk.month != renewal_month:
                    p *= 0.03
                if wk.year == 2026 and wk.month == 10:
                    oracle[acc_id] = p
                    labels[acc_id] = 1 if rng.random() < p else 0
                    break
                if rng.random() < p:
                    last = (dt.date(2026, wk.month % 12 + 1, 1) - dt.timedelta(days=1)).day
                    canceled_at = dt.date(2026, wk.month, rng.randint(1, last))
                    # activity stops at the cancellation week
                    break
            elif w == 0:
                month_seen.add(wk.month)
            if w >= NW:
                break
            # evolve health
            if decline_left == 0 and rng.random() < 0.012:
                decline_left, decline_rate = rng.randint(4, 10), rng.uniform(0.12, 0.25)
            h += -0.05 * h + rng.gauss(0, 0.08)
            if decline_left > 0:
                h -= decline_rate
                decline_left -= 1
            if not champ_gone and rng.random() < 0.006:
                champ_gone = True
            hist.append(h)
            for (u, role, lam, dormant) in u_list:
                if dormant or (role == "admin" and champ_gone):
                    continue
                s = pois(lam * math.exp(0.8 * h))
                if s > 0:
                    activity.append({"week_start": str(wk), "user_id": u, "account_id": acc_id, "sessions": s,
                                     "key_actions": pois(s * 1.5)})
            # tickets
            sq = math.sqrt(n_users)
            for cat, rate in (("billing", 0.012 + 0.05 * max(0.0, -h)), ("bug", 0.03 * sq),
                              ("how_to", 0.025 * sq), ("feature_request", 0.015 * sq)):
                if rng.random() < min(0.9, rate):
                    tid += 1
                    if cat == "billing":
                        billing_weeks.append(w)
                    tickets.append({"ticket_id": "T%06d" % tid, "account_id": acc_id,
                                    "created_at": str(wk + dt.timedelta(days=rng.randrange(7))),
                                    "category": cat, "priority": rng.choice(["low", "normal", "normal", "high"])})
        if annual:
            # next renewal date on or after 2026-10-01
            y = 2026 if renewal_month >= 10 else 2027
            nxt = dt.date(y, renewal_month, min(signup.day, 28))
        else:
            nxt = dt.date(2026, 10, min(signup.day, 28))
        accounts.append({"account_id": acc_id, "plan": plan, "seats": seats, "mrr_usd": mrr,
                         "contract": "annual" if annual else "monthly",
                         "next_renewal_date": "" if canceled_at else str(nxt),
                         "signup_date": str(signup), "region": region, "industry": industry,
                         "canceled_at": str(canceled_at) if canceled_at else ""})

    def dump(name, rows):
        with open(os.path.join(FIX, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    activity.sort(key=lambda r: (r["week_start"], r["account_id"], r["user_id"]))
    tickets.sort(key=lambda r: r["created_at"])
    dump("accounts.csv", accounts)
    dump("users.csv", users)
    dump("weekly_activity.csv", activity)
    dump("support_tickets.csv", tickets)
    with open(os.path.join(HERE, "labels.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["account_id", "churned_oct_2026"])
        for k in sorted(labels):
            w.writerow([k, labels[k]])

    ids = sorted(labels)
    y = [labels[i] for i in ids]
    # naive baseline: fewest sessions in the last 4 weeks
    last4 = {str(WEEKS[-k]) for k in range(1, 5)}
    s4 = {}
    for r in activity:
        if r["week_start"] in last4:
            s4[r["account_id"]] = s4.get(r["account_id"], 0) + r["sessions"]
    naive = [-s4.get(i, 0) for i in ids]
    hist_churn = sum(1 for a in accounts if a["canceled_at"])
    truth = {"n_active": len(ids), "n_churn_oct": sum(y), "base_rate": round(sum(y) / len(ids), 4),
             "oracle_auc": round(auc([oracle[i] for i in ids], y), 4),
             "naive_auc_low_sessions_last4wk": round(auc(naive, y), 4),
             "historical_cancellations_apr_sep": hist_churn,
             "oracle_p_at_100": sum(labels[i] for i in sorted(ids, key=lambda i: -oracle[i])[:100]) / 100}
    with open(os.path.join(HERE, "truth.json"), "w") as f:
        json.dump(truth, f, indent=2)
    print(json.dumps(truth, indent=2), len(activity), len(tickets))


if __name__ == "__main__":
    main()
