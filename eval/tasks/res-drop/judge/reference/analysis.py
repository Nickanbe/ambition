"""Reference analysis for res-drop (stdlib only).  python3 -I analysis.py <fixture_dir> [out_dir]

Method: decompose the Feb->Mar 2026 drop in daily signup events.
 1. Reconcile analytics events against billing accounts by user_id. Accounts
    without an event = measurement loss; locate it by browser (via the event
    mix before the gap) and date.
 2. For real (billing) signups, compare each segment's Mar/Feb change to the
    same change in 2025 (seasonal baseline) and look for price_shown changes.
 3. What is left is unexplained noise.
"""
import csv, collections, json, os, sys

fx = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "."
DAYS = {(2025, 2): 28, (2025, 3): 31, (2026, 2): 28, (2026, 3): 31}

ev = list(csv.DictReader(open(os.path.join(fx, "signups.csv"))))
bill = list(csv.DictReader(open(os.path.join(fx, "billing_accounts.csv"))))
ym = lambda ts: (int(ts[:4]), int(ts[5:7]))

def daily(rows, tkey, y, m, f=lambda r: True):
    return sum(1 for r in rows if ym(r[tkey]) == (y, m) and f(r)) / DAYS[(y, m)]

feb, mar = daily(ev, "event_time", 2026, 2), daily(ev, "event_time", 2026, 3)
drop = feb - mar
seen = {r["user_id"] for r in ev}
missing = [b for b in bill if b["user_id"] not in seen]
miss_mar = sum(1 for b in missing if ym(b["created_at"]) == (2026, 3)) / 31
first_missing = min(b["created_at"] for b in missing)[:10] if missing else None
# which browser vanished: compare version mix of events after the gap starts
def mix(rows):
    c = collections.Counter((r["browser"], r["browser_version"]) for r in rows)
    n = sum(c.values()); return {k: v / n for k, v in c.items()}
before = mix([r for r in ev if "2026-02-01" <= r["event_time"] < "2026-03-01"])
after = mix([r for r in ev if r["event_time"] >= "2026-03-03"])
vanished = [k for k in before if after.get(k, 0) < 0.1 * before[k]]

# price: IN price_shown and IN real signups vs seasonal baseline
def bdaily(y, m, c): return daily(bill, "created_at", y, m, lambda r: r["country"] == c)
seas = (daily(bill, "created_at", 2025, 3) / daily(bill, "created_at", 2025, 2))
other_ratio = (sum(bdaily(2026, 3, c) for c in ["US","GB","DE","BR","CA","AU"]) /
               sum(bdaily(2026, 2, c) for c in ["US","GB","DE","BR","CA","AU"]))
in_expected = bdaily(2026, 2, "IN") * other_ratio
in_loss_real = in_expected - bdaily(2026, 3, "IN")
tracked_frac = 1 - miss_mar / daily(bill, "created_at", 2026, 3)
price_loss_obs = in_loss_real * tracked_frac
prices = sorted({(r["event_time"][:7], r["price_shown_usd"]) for r in ev if r["country"] == "IN" and r["event_time"] >= "2026-01"})

ps = lambda c, y: daily(ev, "event_time", y, 3, lambda r: r["channel"] == c) / daily(ev, "event_time", y, 2, lambda r: r["channel"] == c) - 1

ts, pr = miss_mar / drop, price_loss_obs / drop
answer = {
  "causes": [
    {"description": "Tracking bug: signup events from %s %s stopped being recorded from %s; the accounts were still created in billing (signups happened, analytics lost them)." % (vanished[0][0], vanished[0][1], first_missing),
     "share_of_drop": round(ts, 3)},
    {"description": "Price increase in IN (India): pro price shown rose %s; real IN signups fell ~%.0f%% vs the trend in other countries." % (prices, 100 * in_loss_real / in_expected),
     "share_of_drop": round(pr, 3)},
    {"description": "Residual / noise: small across-the-board dip within normal variation.",
     "share_of_drop": round(1 - ts - pr, 3)},
  ],
  "not_causes": [
    {"description": "paid_social decline is seasonal: Mar vs Feb was %.0f%% in 2025 too, offset by organic_search; total signups were flat Feb->Mar 2025 (%.1f%%)." % (100 * ps("paid_social", 2025), 100 * (seas - 1)),
     "share_of_drop": 0}
  ],
  "observed_drop_pct": round(drop / feb, 4),
  "real_drop_pct_billing": round(1 - daily(bill, "created_at", 2026, 3) / daily(bill, "created_at", 2026, 2), 4),
}
json.dump(answer, open(os.path.join(out, "answer.json"), "w"), indent=2)
print(json.dumps(answer, indent=2))
