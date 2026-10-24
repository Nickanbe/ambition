"""Judge for feat-perf.  Usage: python3 -I judge/judge.py <workdir>

Prints one JSON line {"score": 0..1, "checks": {...}}.

Correctness: merge_contacts must return exactly what the original
implementation (judge/oracle/, a pristine copy of the fixture) returns on 60
hidden randomized cases plus edge cases, must not mutate its input, and must
match the oracle on both benchmark workloads.

Speed: two workloads, each timed against the oracle in this same run on this
same machine (so the score is a ratio, not wall-clock limits):
  many     2,500 records, ~1,500 distinct emails (index/rescan hot spots)
  hot      6,000 records for one account with unique tags + notes
           (tag-list membership and note concatenation hot spots)
Curve per workload: <=1.2x -> 0, 2x -> 0.3, 100x -> 1.0 (log between), then
averaged.

Score = 0.3 * fraction_of_cases_correct + 0.7 * speed (speed counts only
when every correctness check passes).
"""

import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORACLE = os.path.join(HERE, "oracle")

HARNESS = r'''
import copy, hashlib, json, random, sys, time
root, mode = sys.argv[1], sys.argv[2]
sys.path.insert(0, root)
from contacts import merge_contacts

def variant(rng, email):
    r = rng.random()
    if r < 0.2: return email.upper()
    if r < 0.3: return " " + email + " "
    if r < 0.35: return email.replace("@", " @")
    return email

def wl_many(n=2500, seed=11):
    rng = random.Random(seed)
    pool = ["user%d@example%d.com" % (i, i % 37) for i in range(int(n * 0.6))]
    vocab = ["tag%d" % i for i in range(50)]
    out = []
    for i in range(n):
        rec = {"name": ("Person %d" % i) if rng.random() < 0.8 else "",
               "phone": ("555-%07d" % rng.randrange(10**7)) if rng.random() < 0.5 else None,
               "tags": rng.sample(vocab, rng.randrange(4))}
        rec["email"] = None if rng.random() < 0.1 else variant(rng, rng.choice(pool))
        if rng.random() < 0.3:
            rec["note"] = "note %d" % i
        out.append(rec)
    return out

def wl_hot(k=6000, seed=12):
    rng = random.Random(seed)
    return [{"email": variant(rng, "ops@bigcustomer.com"), "name": "Big Customer" if i == 0 else "",
             "tags": ["campaign-%d-%d" % (i, j) for j in range(4)],
             "note": "touchpoint %d: " % i + "x" * 40} for i in range(k)]

def random_case(rng):
    n = rng.randrange(0, 60)
    pool = ["a@x.com", "B@x.com", "c@y.org", "d@y.org", "e@z.net", "f@z.net"]
    tags = ["vip", "VIP ", " beta", "lead", "", "Newsletter", "newsletter", "x"]
    out = []
    for i in range(n):
        rec = {}
        r = rng.random()
        if r < 0.15: rec["email"] = None
        elif r < 0.2: rec["email"] = ""
        elif r < 0.25: rec["email"] = "   "
        elif r < 0.3: pass
        else: rec["email"] = variant(rng, rng.choice(pool))
        if rng.random() < 0.7: rec["name"] = rng.choice(["", " ", "Ann", " Bob ", "Cy", None])
        if rng.random() < 0.6: rec["phone"] = rng.choice(["", None, "+1 (555) 000-1111", "5550001111", "15550002222", "555.000.3333", 5550004444])
        if rng.random() < 0.8: rec["tags"] = rng.sample(tags, rng.randrange(0, 4))
        elif rng.random() < 0.5: rec["tags"] = None
        if rng.random() < 0.5: rec["note"] = rng.choice(["", "  ", "hello", " call back ", None, "line one\nline two"])
        out.append(rec)
    return out

def run_one(records):
    before = copy.deepcopy(records)
    try:
        res = merge_contacts(records)
        res = json.loads(json.dumps(res, sort_keys=True, default=repr))
        out = json.dumps(res, sort_keys=True)
    except Exception as exc:
        out = "ERROR " + type(exc).__name__ + ": " + str(exc)[:80]
    return out, records == before

if mode == "cases":
    rng = random.Random(20261024)
    cases = [[], [{}], [{"email": None}], [{"email": "A@b.c"}, {"email": "a@B.C", "tags": ["T", "t"]}]]
    cases += [random_case(rng) for _ in range(60)]
    results = []
    for c in cases:
        out, unmutated = run_one(c)
        results.append([out, unmutated])
    print(json.dumps(results))
else:
    records = wl_many() if mode == "many" else wl_hot()
    repeats = int(sys.argv[3])
    best = None
    out = None
    for _ in range(repeats):
        data = copy.deepcopy(records)
        t = time.perf_counter()
        res = merge_contacts(data)
        dt = time.perf_counter() - t
        best = dt if best is None else min(best, dt)
        if out is None:
            out = hashlib.sha256(json.dumps(res, sort_keys=True, default=repr).encode()).hexdigest()
        if best > 5:
            break
    print(json.dumps({"seconds": best, "sha": out}))
'''


def child(root, mode, *extra, timeout=180):
    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-c", HARNESS, root, mode] + list(extra),
                           capture_output=True, text=True, timeout=timeout, cwd=root)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    try:
        return json.loads(p.stdout.strip().splitlines()[-1]), ""
    except Exception:
        return None, (p.stderr or p.stdout)[-300:]


def curve(speedup):
    if speedup <= 1.2:
        return 0.0
    if speedup < 2:
        return 0.3 * (speedup - 1.2) / 0.8
    return min(1.0, 0.3 + 0.7 * math.log(speedup / 2) / math.log(50))


def main():
    wd = os.path.abspath(sys.argv[1])
    checks = {}

    want, _ = child(ORACLE, "cases")
    got, err = child(wd, "cases", timeout=120)
    if got is None or len(got) != len(want):
        case_frac, unmutated = 0.0, False
        checks["cases_error"] = err
    else:
        matches = [g[0] == w[0] for g, w in zip(got, want)]
        case_frac = sum(matches) / len(matches)
        unmutated = all(g[1] for g in got)
        bad = [i for i, m in enumerate(matches) if not m]
        if bad:
            checks["first_mismatch"] = {"case": bad[0], "got": got[bad[0]][0][:200], "want": want[bad[0]][0][:200]}
    checks["cases_correct"] = round(case_frac, 3)
    checks["input_not_mutated"] = unmutated

    speed_parts = []
    bench_ok = True
    for mode in ("many", "hot"):
        base, _ = child(ORACLE, mode, "1")
        cand, err = child(wd, mode, "3", timeout=120)
        if cand is None:
            bench_ok = False
            checks[mode] = {"error": err[-200:]}
            speed_parts.append(0.0)
            continue
        sp = base["seconds"] / max(cand["seconds"], 1e-6)
        same = cand["sha"] == base["sha"]
        bench_ok = bench_ok and same
        speed_parts.append(curve(sp))
        checks[mode] = {"baseline_s": round(base["seconds"], 3), "candidate_s": round(cand["seconds"], 4),
                        "speedup": round(sp, 1), "output_matches": same, "curve": round(curve(sp), 3)}

    all_correct = case_frac == 1.0 and unmutated and bench_ok
    speed = sum(speed_parts) / len(speed_parts)
    checks["all_correct"] = all_correct
    checks["speed"] = round(speed, 3)
    score = 0.3 * case_frac + (0.7 * speed if all_correct else 0.0)
    print(json.dumps({"score": round(score, 3), "checks": checks}))


if __name__ == "__main__":
    main()
