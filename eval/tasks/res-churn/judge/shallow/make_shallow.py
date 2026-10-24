"""Literal 'shallow analyst' rankings for validating the judge.
python3 -I make_shallow.py <fixture_dir> <shallow_dir>
  low_activity: fewest sessions in the last 4 weeks of data.
  low_activity_per_seat: same, divided by seats.
"""
import csv, collections, json, os, sys
fx, out = sys.argv[1], sys.argv[2]
acc = {a["account_id"]: a for a in csv.DictReader(open(os.path.join(fx, "accounts.csv")))}
act = list(csv.DictReader(open(os.path.join(fx, "weekly_activity.csv"))))
last4 = sorted({r["week_start"] for r in act})[-4:]
s = collections.Counter()
for r in act:
    if r["week_start"] in last4:
        s[r["account_id"]] += int(r["sessions"])
active = [a for a in acc if not acc[a]["canceled_at"]]
for name, key in (("low_activity", lambda a: s[a]), ("low_activity_per_seat", lambda a: s[a] / int(acc[a]["seats"]))):
    rk = sorted(active, key=key)
    json.dump({"ranking": [{"account_id": a, "score": round(1 - i / len(rk), 4)} for i, a in enumerate(rk)]},
              open(os.path.join(out, name, "answer.json"), "w"))
