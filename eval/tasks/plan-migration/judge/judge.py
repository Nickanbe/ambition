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


SIX = r"(06:00|\b6:00|\b0?6 ?am\b|\b0?6 ?a\.m\.)"


def checks_for(t):
    grounded = [
        r"\b33\s*(of|/|out of)\s*60|\b33 nights",                 # overlap nights
        r"\b7\s*(deadlocks|nights|of|/|times)|seven deadlocks",      # deadlocks
        r"\b6\s*(of|/|out of)\s*60|\b10\s*%|six nights|\b6 nights",  # silent export failures
        r"\b2\s*(of|/|out of)\s*60|\btwo nights|\b2 nights|09-14|10-12|sept(ember)? 14|oct(ober)? 12",  # missed deadline
        r"\b51 accounts|inc-2291|09-30|sept(ember)? 30",           # double late fees
        r"05:4\d|05:5\d|\b1[0-2] nights|\b168|\b116",               # deadline margin
    ]
    return {
        "overlap_contention": near(t, r"(sync_inventory|inventory)", r"(rebuild_search|search[_ ]index|search)")
            and near(t, r"(products|sync_inventory|rebuild_search|inventory)",
                     r"(lock|contend|contention|overlap|deadlock|concurren|serializ|mutual|mutex|same table|conflict)"),
        "silent_failure": near(t, r"(export_orders|export orders|orders? export|sftp)",
            r"(silent|exit[ =]?0|exit code|exit status|\|\| ?true|swallow|mask|false success|reports? success|\btee\b|pipefail|error in (the )?log|logs? (an )?error|not delivered|\b10\s*%|\b6\s*(of|/)\s*60|six nights)"),
        "non_idempotent_retry": near(t, r"(apply_late_fees|late[ -]fees?)",
            r"(idempot|double|twice|duplicate|dedup|exactly[- ]once|at[- ]least[- ]once|unique (key|constraint|index)|guard|inc-2291)"),
        "hard_6am_deadline": near(t, SIX, r"(aggregate|daily_sales|daily sales|finance_report|finance report|cfo)")
            and near(t, SIX, r"(deadline|sla|alert|priority|must|before|latest|budget|page|miss)"),
        "grounded_in_log": sum(1 for p in grounded if re.search(p, t)) >= 2,
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
