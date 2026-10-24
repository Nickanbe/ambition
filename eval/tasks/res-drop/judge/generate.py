"""Seeded generator for res-drop. Writes fixture/*.csv and judge/truth.json.

Planted ground truth (Feb 2026 -> Mar 2026, daily signup events):
  * Tracking bug: from 2026-03-03, signup events from Safari 19.3 stop being
    recorded. The accounts were still created (billing_accounts.csv has them).
    ~60% of the observed drop.
  * Price increase: pro price shown in IN goes 8 -> 12 USD on 2026-03-01;
    IN signups fall ~30%. Real loss. ~30% of the drop.
  * Noise: a 2% across-the-board dip. ~10%.
  * Red herring: paid_social falls ~30% every March (2025 too), offset by an
    organic_search rise. Seasonal, not a cause.

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
rng = random.Random(20261024)

COUNTRIES = [("US", 0.30), ("IN", 0.20), ("GB", 0.12), ("DE", 0.10), ("BR", 0.10), ("CA", 0.08), ("AU", 0.10)]
PRO_PRICE = {"US": 20, "IN": 8, "GB": 18, "DE": 18, "BR": 10, "CA": 19, "AU": 19}
PLANS = [("free", 0.62), ("pro", 0.30), ("team", 0.08)]
BASE_CH = {"organic_search": 0.35, "paid_social": 0.25, "paid_search": 0.15, "referral": 0.15, "email": 0.10}


def channel_mix(month):
    m = dict(BASE_CH)
    if month == 3:  # seasonal: paid social budget pause every March, organic picks up
        m["paid_social"] = 0.25 * 0.70
        m["organic_search"] = 0.35 + 0.25 * 0.30
    return list(m.items())


def browser_mix(day):
    # Safari 19.3 ~13% of traffic in 2026; older versions in 2025
    if day.year == 2026:
        return [("Chrome", "141", 0.38), ("Chrome", "140", 0.12), ("Safari", "19.3", 0.13),
                ("Safari", "19.2", 0.07), ("Edge", "141", 0.12), ("Firefox", "143", 0.10),
                ("Samsung Internet", "28", 0.08)]
    return [("Chrome", "133", 0.38), ("Chrome", "132", 0.12), ("Safari", "18.3", 0.13),
            ("Safari", "18.2", 0.07), ("Edge", "133", 0.12), ("Firefox", "135", 0.10),
            ("Samsung Internet", "27", 0.08)]


def pick(items, wi=-1):
    r = rng.random()
    acc = 0.0
    for it in items:
        acc += it[wi]
        if r <= acc:
            return it
    return items[-1]


def pois(mu):
    return max(0, int(round(rng.gauss(mu, math.sqrt(mu)))))


BUG_START = dt.date(2026, 3, 3)
PRICE_START = dt.date(2026, 3, 1)


def days(y):
    d = dt.date(y, 1, 1)
    while d <= dt.date(y, 3, 31):
        yield d
        d += dt.timedelta(days=1)


def main():
    ev_rows, bill_rows = [], []
    uid = 100000
    lost_tracking = 0
    for year, base in ((2025, 330.0), (2026, 400.0)):
        for d in days(year):
            wk = 0.82 if d.weekday() >= 5 else 1.07
            mu = base * wk
            if year == 2026 and d.month == 3:
                mu *= 0.98  # noise dip
            # draw candidate visitors-who-would-sign-up; price effect thins IN
            n = pois(mu)
            for _ in range(n):
                country = pick(COUNTRIES)[0]
                price = PRO_PRICE[country]
                if country == "IN" and d >= PRICE_START:
                    price = 12
                    if rng.random() < 0.30:
                        continue  # lost to price increase
                ch = pick(channel_mix(d.month))[0]
                br, ver, _ = pick(browser_mix(d))
                plan = pick(PLANS)[0]
                uid += 1
                user = "u%d" % uid
                ts = dt.datetime(d.year, d.month, d.day) + dt.timedelta(seconds=rng.randrange(86400))
                bill_rows.append({"account_id": "acct_%d" % uid, "user_id": user,
                                  "created_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
                                  "country": country, "plan": plan,
                                  "monthly_price_usd": 0 if plan == "free" else (price if plan == "pro" else price * 3)})
                if br == "Safari" and ver == "19.3" and d >= BUG_START:
                    lost_tracking += 1
                    continue  # event never reaches analytics
                ev_rows.append({"event_time": ts.strftime("%Y-%m-%d %H:%M:%S"), "user_id": user,
                                "browser": br, "browser_version": ver, "country": country,
                                "channel": ch, "plan": plan, "price_shown_usd": price})
    ev_rows.sort(key=lambda r: r["event_time"])
    bill_rows.sort(key=lambda r: r["created_at"])
    with open(os.path.join(FIX, "signups.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ev_rows[0].keys()))
        w.writeheader()
        w.writerows(ev_rows)
    with open(os.path.join(FIX, "billing_accounts.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(bill_rows[0].keys()))
        w.writeheader()
        w.writerows(bill_rows)

    # realized truth
    def daily(rows, key, y, m, pred=lambda r: True):
        n = sum(1 for r in rows if r[key].startswith("%d-%02d" % (y, m)) and pred(r))
        nd = (dt.date(y, m % 12 + 1, 1) - dt.timedelta(days=1)).day if m < 12 else 31
        return n / nd

    feb = daily(ev_rows, "event_time", 2026, 2)
    mar = daily(ev_rows, "event_time", 2026, 3)
    drop = feb - mar
    track = lost_tracking / 31.0
    # price loss: expected IN loss = IN Feb daily (billing, true) * 0.98 noise * 0.30 / 0.70 relation
    in_feb = daily(bill_rows, "created_at", 2026, 2, lambda r: r["country"] == "IN")
    in_mar = daily(bill_rows, "created_at", 2026, 3, lambda r: r["country"] == "IN")
    price_loss = in_feb * 0.98 - in_mar  # vs. what IN would have been with only the noise dip
    # observed-in-events share (tracked fraction of IN loss); approx: price loss scaled by 1-0.13
    price_loss_obs = price_loss * (1 - 0.13 * 29 / 31)
    truth = {
        "feb_daily_events": round(feb, 2), "mar_daily_events": round(mar, 2),
        "drop_pct": round(drop / feb, 4),
        "tracking_share": round(track / drop, 3),
        "price_share": round(price_loss_obs / drop, 3),
        "noise_share": round(1 - track / drop - price_loss_obs / drop, 3),
        "billing_drop_pct": round(1 - daily(bill_rows, "created_at", 2026, 3) / daily(bill_rows, "created_at", 2026, 2), 4),
        "bug_browser": "Safari 19.3", "bug_start": str(BUG_START),
        "price_country": "IN", "red_herring_channel": "paid_social",
        "paid_social_mar_vs_feb_2026": round(
            daily(ev_rows, "event_time", 2026, 3, lambda r: r["channel"] == "paid_social") /
            daily(ev_rows, "event_time", 2026, 2, lambda r: r["channel"] == "paid_social") - 1, 3),
        "paid_social_mar_vs_feb_2025": round(
            daily(ev_rows, "event_time", 2025, 3, lambda r: r["channel"] == "paid_social") /
            daily(ev_rows, "event_time", 2025, 2, lambda r: r["channel"] == "paid_social") - 1, 3),
        "total_mar_vs_feb_2025": round(daily(ev_rows, "event_time", 2025, 3) / daily(ev_rows, "event_time", 2025, 2) - 1, 4),
    }
    with open(os.path.join(HERE, "truth.json"), "w") as f:
        json.dump(truth, f, indent=2)
    print(json.dumps(truth, indent=2))


if __name__ == "__main__":
    main()
