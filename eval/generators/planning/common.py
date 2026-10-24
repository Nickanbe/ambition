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
