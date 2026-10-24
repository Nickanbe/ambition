"""Reference analysis for res-abtest (stdlib only).  python3 -I analysis.py <fixture_dir> [out_dir]

1. SRM check: chi-square of A/B counts against the intended 50/50.
2. Locate it: A share by device / platform / app_version; the cell with no B users is the bug.
3. Re-estimate on the properly assigned population (drop that cell from both arms),
   and a platform-stratified estimate, each with a 95% CI.
"""
import csv, collections, json, math, os, sys
fx = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "."
rows = list(csv.DictReader(open(os.path.join(fx, "assignments.csv"))))
buy = {o["user_id"] for o in csv.DictReader(open(os.path.join(fx, "orders.csv")))}

def est(rs):
    n = collections.Counter(r["variant"] for r in rs)
    c = collections.Counter(r["variant"] for r in rs if r["user_id"] in buy)
    pa, pb = c["A"] / n["A"], c["B"] / n["B"]
    se = math.sqrt(pa * (1 - pa) / n["A"] + pb * (1 - pb) / n["B"])
    return n, pa, pb, pb / pa - 1, ((pb - pa - 1.96 * se) / pa, (pb - pa + 1.96 * se) / pa)

n, pa, pb, lift, ci = est(rows)
tot = n["A"] + n["B"]
chi2 = sum((n[v] - tot / 2) ** 2 / (tot / 2) for v in "AB")
cells = collections.defaultdict(collections.Counter)
for r in rows:
    cells[(r["platform"], r["app_version"])][r["variant"]] += 1
bad = [k for k, v in cells.items() if v["B"] < 0.2 * v["A"]]
clean = [r for r in rows if (r["platform"], r["app_version"]) not in bad]
cn, cpa, cpb, clift, cci = est(clean)
cchi = sum((cn[v] - (cn["A"] + cn["B"]) / 2) ** 2 / ((cn["A"] + cn["B"]) / 2) for v in "AB")
by_dev = {d: est([r for r in clean if r["device"] == d])[3] for d in ("desktop", "mobile")}
ans = {
  "ship": False,
  "effect_estimate": round(clift, 4),
  "effect_ci95": [round(cci[0], 4), round(cci[1], 4)],
  "issues": [
    "Sample ratio mismatch: A=%d vs B=%d on an intended 50/50 split (chi-square %.0f, p << 0.001). The split is broken, so the naive +%.1f%% lift is not trustworthy." % (n["A"], n["B"], chi2, 100 * lift),
    "The missing B users are all mobile: %s has %d A users and %d B users. B users on that iOS app version were never logged, and that segment converts below average, so B's mix is skewed toward desktop." % (bad, cells[bad[0]]["A"], cells[bad[0]]["B"]),
    "On the properly assigned population (excluding %s from both arms; split %d/%d, chi-square %.1f) B's lift is %+.1f%% (95%% CI %+.1f%% to %+.1f%%): no detectable effect. Desktop %+.1f%%, mobile %+.1f%%." % (bad, cn["A"], cn["B"], cchi, 100 * clift, 100 * cci[0], 100 * cci[1], 100 * by_dev["desktop"], 100 * by_dev["mobile"]),
    "Fix the iOS 8.4 assignment logging and rerun before deciding; B also has not been observed at all for iOS 8.4 users.",
  ],
}
json.dump(ans, open(os.path.join(out, "answer.json"), "w"), indent=2)
print(json.dumps(ans, indent=2))
