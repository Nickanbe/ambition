import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "fixture_manifest.json")  # {relpath: sha256} of the pristine fixture
PLAN_NAMES = ("plan.md", "PLAN.md", "Plan.md")


def fixture_manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def fixture_files():
    return set(fixture_manifest())


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_plan(workdir):
    """plan.md if written; otherwise any new top-level .md/.txt the arm wrote."""
    for n in PLAN_NAMES:
        p = os.path.join(workdir, n)
        if os.path.isfile(p):
            return open(p, encoding="utf-8", errors="replace").read(), n
    known = fixture_files()
    parts, names = [], []
    for n in sorted(os.listdir(workdir)):
        p = os.path.join(workdir, n)
        if os.path.isfile(p) and n not in known and n.lower().endswith((".md", ".txt")):
            parts.append(open(p, encoding="utf-8", errors="replace").read())
            names.append(n)
    return "\n".join(parts), ",".join(names)


def norm(text):
    text = text.lower().replace("‑", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[*`]+", "", text)


def near(text, a, b, window=350):
    """True when regex a and regex b both match within `window` chars of each other."""
    for m in re.finditer(a, text):
        seg = text[max(0, m.start() - window): m.end() + window]
        if re.search(b, seg):
            return True
    return False


def emit(checks, source):
    score = sum(1 for v in checks.values() if v) / len(checks) if checks else 0.0
    print(json.dumps({"score": round(score, 3), "checks": checks, "source": source}))


def checks_for(t):
    grounded = [
        r"\b1,?511\b", r"\b1,?212\b", r"\b299\b", r"\b396\b|\b304\b", r"\b197\b|\b155\b",
        r"\b190\b", r"\b18\.5\s*%", r"\b4\.1\s*%", r"\$?6,?060\b", r"\b349\b",
    ]
    return {
        "annual_contracts_grandfathered": near(t, r"(annual|contract)",
            r"(grandfather|renewal|renew|price[_ ]locked|locked|honou?r|exempt|until|term|contract_end|8\.1|\b299\b)"),
        "eu_30_day_notice": near(t, r"(\beu\b|europe|\beea\b)", r"(\b30[- ]?days?|thirty|8\.2)"),
        "heavy_single_seat_downgrade": near(t, r"(starter|downgrad)",
            r"(heavy|power[- ]users?|high[- ]usage|single[- ]seat|\b1[- ]seat|one[- ]seat|solo|no integrations|without integrations|don'?t use integrations|integrations_used|\b197\b|\b155\b)"),
        "new_tenure_churn_2024": near(t,
            r"(tenure|new(er)? (pro )?(customers|signups|sign-ups|subscribers|users|accounts)|month[- ]?1\b|(in )?their first (30 days|month|60 days|two months|weeks?)|first[- ]month (customers|cohort|users|subscribers)|0[-–]1 months?|recent(ly)? (sign|join)|signed up (in the )?(last|past)|\btrial)",
            r"(churn|2024|spike|last time|previous|18\.5|concentrat|exempt|protect)"),
        "grounded_in_data": sum(1 for p in grounded if re.search(p, t)) >= 3,
    }


def main():
    workdir = sys.argv[1]
    text, src = read_plan(workdir)
    if not text.strip():
        emit({k: False for k in checks_for("")}, src or "none")
        return
    emit(checks_for(norm(text)), src)


if __name__ == "__main__":
    main()
