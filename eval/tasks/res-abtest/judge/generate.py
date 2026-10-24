"""Seeded generator for res-abtest. Writes fixture/*.csv and judge/truth.json.

Planted ground truth:
  * Intended 50/50 split of users reaching checkout, 2026-09-01 .. 2026-09-28.
  * True treatment effect is zero in every segment.
  * Assignment bug: users bucketed into B on iOS app version 8.4 are never
    logged (the B checkout crashed the 8.4 logging SDK). ~30% of mobile users
    are therefore missing from B only -> sample ratio mismatch.
  * Those users convert below average, so B's naive conversion is inflated by
    composition (~ +4% relative). Within properly assigned segments the lift is ~0.

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

N = 130000
CONV = {"web_desktop": 0.42, "web_mobile": 0.26, "ios_app": 0.26, "android_app": 0.28}
IOS_VERS = [("8.4", 0.84), ("8.3", 0.11), ("8.2", 0.05)]
AND_VERS = [("8.4", 0.70), ("8.3", 0.20), ("8.1", 0.10)]


def pick(rng, items):
    r, acc = rng.random(), 0.0
    for k, w in items:
        acc += w
        if r <= acc:
            return k
    return items[-1][0]


def build(seed):
    rng = random.Random(seed)
    rows, orders = [], []
    t0 = dt.datetime(2026, 9, 1)
    oid = 0
    for i in range(N):
        dev = "desktop" if rng.random() < 0.5 else "mobile"
        if dev == "desktop":
            plat, ver = "web", ""
            seg = "web_desktop"
        else:
            plat = pick(rng, [("web", 0.40), ("ios_app", 0.35), ("android_app", 0.25)])
            if plat == "web":
                ver, seg = "", "web_mobile"
            elif plat == "ios_app":
                ver, seg = pick(rng, IOS_VERS), "ios_app"
            else:
                ver, seg = pick(rng, AND_VERS), "android_app"
        var = "A" if rng.random() < 0.5 else "B"
        conv = rng.random() < CONV[seg]
        if var == "B" and plat == "ios_app" and ver == "8.4":
            continue  # never logged
        uid = "c%06d" % (i + 1)
        ts = t0 + dt.timedelta(seconds=rng.randrange(28 * 86400))
        rows.append({"user_id": uid, "variant": var, "assigned_at": ts.strftime("%Y-%m-%d %H:%M:%S"),
                     "device": dev, "platform": plat, "app_version": ver,
                     "country": pick(rng, [("US", 0.5), ("GB", 0.15), ("DE", 0.12), ("FR", 0.1), ("CA", 0.13)])})
        if conv:
            oid += 1
            orders.append({"order_id": "o%06d" % oid, "user_id": uid,
                           "ordered_at": (ts + dt.timedelta(minutes=rng.randint(1, 90))).strftime("%Y-%m-%d %H:%M:%S"),
                           "order_value_usd": round(math.exp(rng.gauss(4.0, 0.5)), 2)})
    return rows, orders


def stats(rows, orders, keep=lambda r: True):
    buyers = {o["user_id"] for o in orders}
    n = {"A": 0, "B": 0}
    c = {"A": 0, "B": 0}
    for r in rows:
        if keep(r):
            n[r["variant"]] += 1
            c[r["variant"]] += r["user_id"] in buyers
    ca, cb = c["A"] / n["A"], c["B"] / n["B"]
    return n, ca, cb, cb / ca - 1


def main():
    # pick the first seed whose naive lift reads ~4% and clean lift ~0 (documented, deterministic)
    found = False
    for seed in range(1000, 1400):
        rows, orders = build(seed)
        n, ca, cb, lift = stats(rows, orders)
        _, _, _, clean = stats(rows, orders, lambda r: not (r["platform"] == "ios_app" and r["app_version"] == "8.4"))
        if 0.037 <= lift <= 0.043 and abs(clean) <= 0.004:
            found = True
            break
    assert found, 'no seed matched'
    rows.sort(key=lambda r: r["assigned_at"])
    orders.sort(key=lambda r: r["ordered_at"])
    for name, data in (("assignments.csv", rows), ("orders.csv", orders)):
        with open(os.path.join(FIX, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
    _, _, _, desk = stats(rows, orders, lambda r: r["device"] == "desktop")
    truth = {"seed": seed, "n": n, "conv_A": round(ca, 4), "conv_B": round(cb, 4), "naive_lift": round(lift, 4),
             "clean_lift_excl_ios84": round(clean, 4), "desktop_lift": round(desk, 4), "true_effect": 0.0,
             "srm_chi2": round(((n["A"] - (n["A"] + n["B"]) / 2) ** 2 + (n["B"] - (n["A"] + n["B"]) / 2) ** 2) / ((n["A"] + n["B"]) / 2), 1)}
    json.dump(truth, open(os.path.join(HERE, "truth.json"), "w"), indent=2)
    print(json.dumps(truth, indent=2))


if __name__ == "__main__":
    main()
