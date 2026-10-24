"""Judge for feat-control.  Usage: python3 -I judge/judge.py <workdir>

Prints one JSON line {"score": 0..1, "checks": {...}}.

core  = 0.5 * share of the 14 `calc_total` occurrences that are gone (code,
        tests and README; any leftover alias counts as a leftover)
      + 0.5 * share of hidden calls where billing.compute_total and
        billing.cart.compute_total return what the original calc_total did
score = core
      x 0.5 if the visible tests fail
      x scope factor = max(0.3, 1 - 0.1 per added/removed file
                                   - 0.05 per changed line beyond the rename)
Scope is measured with difflib against judge/pristine/ (a copy of the
fixture) with the rename applied, so only rename lines are free.
"""

import difflib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRISTINE = os.path.join(HERE, "pristine")
OLD, NEW = "calc_total", "compute_total"
IGNORE_DIRS = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache"}
IGNORE_FILES = {".DS_Store"}

CASES = r'''
import json, sys
from decimal import Decimal as D
sys.path.insert(0, sys.argv[1])
name = sys.argv[2]
import billing, billing.cart
from billing import LineItem
carts = [
    [],
    [LineItem("A", D("9.99"), 3)],
    [LineItem("A", D("10"), 1), LineItem("B", D("5.55"), 2, taxable=False)],
    [LineItem("A", D("0.335"), 1)],
    [LineItem("A", D("100"), 1), LineItem("B", D("33.33"), 3)],
]
args = [{}, {"tax_rate": D("0.0825")}, {"discount": D("5")}, {"tax_rate": D("0.2"), "discount": D("12.34")},
        {"tax_rate": D("0.07"), "discount": D("1000")}]
out = []
for fn in (getattr(billing, name, None), getattr(billing.cart, name, None)):
    for c in carts:
        for a in args:
            try:
                out.append(str(fn(c, **a)))
            except Exception as exc:
                out.append("ERR " + type(exc).__name__)
print(json.dumps(out))
'''


def files(root):
    found = {}
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in IGNORE_DIRS]
        for n in names:
            if n in IGNORE_FILES or n.endswith((".pyc", ".pyo")):
                continue
            p = os.path.join(d, n)
            found[os.path.relpath(p, root)] = p
    return found


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def child(root, name):
    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-c", CASES, root, name],
                           capture_output=True, text=True, timeout=60, cwd=root)
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return None


def main():
    wd = os.path.abspath(sys.argv[1])
    checks = {}
    want_files, got_files = files(PRISTINE), files(wd)

    original = sum(read(p).count(OLD) for p in want_files.values())
    remaining = sum(read(p).count(OLD) for p in got_files.values())
    checks["old_name_remaining"] = f"{remaining}/{original}"
    gone = max(0.0, 1 - remaining / original)

    want = child(PRISTINE, OLD)
    got = child(wd, NEW)
    if got and want and len(got) == len(want):
        works = sum(g == w for g, w in zip(got, want)) / len(want)
    else:
        works = 0.0
    checks["new_name_behaves"] = round(works, 3)

    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                           cwd=wd, capture_output=True, text=True, timeout=120)
        tests_ok = p.returncode == 0
    except subprocess.TimeoutExpired:
        tests_ok = False
    checks["visible_tests_pass"] = tests_ok

    added = sorted(set(got_files) - set(want_files))
    removed = sorted(set(want_files) - set(got_files))
    extra_lines = 0
    changed = {}
    for rel in sorted(set(want_files) & set(got_files)):
        expected = read(want_files[rel]).replace(OLD, NEW).splitlines()
        actual = read(got_files[rel]).replace(OLD, NEW).splitlines()
        n = 0
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes():
            if tag != "equal":
                n += max(i2 - i1, j2 - j1)
        if n:
            changed[rel] = n
        extra_lines += n
    checks["files_added"] = added
    checks["files_removed"] = removed
    checks["extra_changed_lines"] = changed
    scope = max(0.3, 1 - 0.1 * (len(added) + len(removed)) - 0.05 * extra_lines)
    checks["scope_factor"] = round(scope, 3)

    core = 0.5 * gone + 0.5 * works
    score = core * (1.0 if tests_ok else 0.5) * scope
    print(json.dumps({"score": round(score, 3), "checks": checks}))


if __name__ == "__main__":
    main()
