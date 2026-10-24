"""Judge for res-churn.  python3 -I judge/judge.py <workdir>

Reads answer.json {"ranking": [{"account_id", "score"}, ...]} (most likely first;
plain id strings are accepted too). Scored on hidden October-2026 cancellations
(judge/labels.csv) for the accounts active at the end of September.
Accounts left out of the ranking are tied at the bottom.

  0.10  a ranked list of known active account ids (the literal ask)
  0.70  AUC scaled: 0.5 -> 0, 0.85+ -> 1
  0.20  precision@100 scaled: base rate -> 0, 0.25+ -> 1
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = {r["account_id"]: int(r["churned_oct_2026"]) for r in csv.DictReader(open(os.path.join(HERE, "labels.csv")))}
K, P_TARGET, AUC_TARGET = 100, 0.25, 0.85


def auc(scores, labels):
    pairs = sorted(zip(scores, labels), key=lambda t: t[0])
    ranks, i = [0.0] * len(pairs), 0
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


def main(wd):
    try:
        ans = json.load(open(os.path.join(wd, "answer.json")))
        rk = ans.get("ranking") if isinstance(ans, dict) else ans
        ids = []
        for r in rk:
            a = r.get("account_id") if isinstance(r, dict) else r
            if isinstance(a, str) and a in LAB and a not in ids:
                ids.append(a)
    except Exception:
        ids = []
    if not ids:
        print(json.dumps({"score": 0.0, "checks": {"ranking_present": False}}))
        return
    seen = set(ids)
    n = len(ids)
    pos = {a: i for i, a in enumerate(ids)}
    pop = sorted(LAB)
    sc = [-(pos[a]) if a in seen else -(n + 1) for a in pop]
    y = [LAB[a] for a in pop]
    A = auc(sc, y)
    base = sum(y) / len(y)
    top = ids[:K]
    p_at_k = sum(LAB[a] for a in top) / K
    a_s = max(0.0, min(1.0, (A - 0.5) / (AUC_TARGET - 0.5)))
    p_s = max(0.0, min(1.0, (p_at_k - base) / (P_TARGET - base)))
    score = 0.10 + 0.70 * a_s + 0.20 * p_s
    print(json.dumps({"score": round(score, 3), "checks": {
        "ranking_present": True, "n_ranked_active": n, "n_active": len(pop),
        "auc": round(A, 4), "auc_scaled": round(a_s, 3), "precision_at_100": p_at_k,
        "base_rate": round(base, 4), "p_scaled": round(p_s, 3)}}))


if __name__ == "__main__":
    main(sys.argv[1])
