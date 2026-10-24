"""Seeded generator for res-control. Writes fixture/orders.csv, judge/truth.json, judge/manifest.json.
Includes a handful of orders at exactly 100.00 (not "over $100").
Run: python3 -I judge/generate.py   (from the task directory)
"""
import csv, datetime as dt, hashlib, json, math, os, random
HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(os.path.dirname(HERE), "fixture")
rng = random.Random(7)
rows = []
for i in range(500):
    amt = round(math.exp(rng.gauss(4.1, 0.6)), 2)
    if rng.random() < 0.02:
        amt = 100.00
    rows.append({"order_id": "ORD-%05d" % (20001 + i),
                 "order_date": str(dt.date(2026, 9, 1) + dt.timedelta(days=rng.randrange(30))),
                 "customer_id": "C%04d" % rng.randrange(1, 900), "amount_usd": "%.2f" % amt})
with open(os.path.join(FIX, "orders.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
gt = sum(1 for r in rows if float(r["amount_usd"]) > 100)
ge = sum(1 for r in rows if float(r["amount_usd"]) >= 100)
json.dump({"count_over_100": gt, "count_at_least_100": ge, "n_orders": len(rows)}, open(os.path.join(HERE, "truth.json"), "w"), indent=2)
man = {}
for root, _, files in os.walk(FIX):
    for fn in files:
        p = os.path.join(root, fn)
        man[os.path.relpath(p, FIX)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
json.dump(man, open(os.path.join(HERE, "manifest.json"), "w"), indent=2)
print(gt, ge)
