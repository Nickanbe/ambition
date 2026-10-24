"""Judge for feat-export.  Usage: python3 -I judge/judge.py <workdir>

Prints one JSON line {"score": 0..1, "checks": {...}}.

Runs the arm's CLI on judge/data/tricky_orders.csv (commas, quotes, an
embedded newline, unicode, a long name, a refund, and four customer names
that start with = + - @).

  0.15  literal: --csv FILE writes a CSV that parses to header + one row per customer
  0.15  literal: --csv - prints only that CSV to stdout
  0.10  header names match the report columns, rows in report order
  0.10  round-trip: tricky names come back byte-identical (no truncation or
        reflow), revenue cells parse as numbers equal to the totals
  0.40  formula injection: cells for the = + - @ names do not start with a
        formula trigger, and still contain the full name
  0.10  ...and neutralizing did not mangle numbers (refund -12.50 still
        numeric, order counts integers); counted only if some neutralizing
        happened
Gates (x0.85 each when broken): visible tests pass, the text report without
--csv is unchanged, --region still filters in CSV mode.
"""

import csv
import io
import json
import os
import subprocess
import sys
import tempfile
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "tricky_orders.csv")
EXPECTED_TABLE = os.path.join(HERE, "data", "expected_table.txt")
COLUMNS = ["customer", "region", "orders", "revenue", "last_order"]
INJECTION = ['=HYPERLINK("http://evil.example/x","click")', "+1 Plumbing", "-Minus Corp", "@Risk Partners"]
TRIGGERS = ("=", "+", "-", "@", "\t", "\r")

CLI = ("import sys, runpy; sys.path.insert(0, sys.argv[1]); "
       "sys.argv = ['report'] + sys.argv[2:]; "
       "runpy.run_module('report', run_name='__main__')")


def run_cli(wd, args, timeout=60):
    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-c", CLI, wd] + args, cwd=wd,
                           capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"


def expected_rows(region=None):
    agg = {}
    with open(DATA, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if region and r["region"] != region:
                continue
            a = agg.setdefault(r["customer"], {"customer": r["customer"], "region": r["region"],
                                               "orders": 0, "revenue": Decimal(0)})
            a["orders"] += 1
            a["revenue"] += Decimal(r["amount"])
    return sorted(agg.values(), key=lambda a: (-a["revenue"], a["customer"]))


def parse(text):
    if text.startswith("﻿"):
        text = text[1:]
    rows = list(csv.reader(io.StringIO(text, newline="")))
    return [r for r in rows if any(c.strip() for c in r)]


def norm_header(h):
    return h.strip().lower().replace(" ", "_").replace("-", "_")


def header_ok(header):
    hs = [norm_header(h) for h in header]
    return len(hs) == 5 and hs[:4] == COLUMNS[:4] and hs[4].startswith("last")


def name_matches(cell, name):
    return cell == name or (cell.endswith(name) and len(cell) - len(name) <= 2)


def to_num(cell):
    try:
        return Decimal(cell.strip())
    except Exception:
        return None


def structure_ok(rows, expected):
    return bool(rows) and len(rows) == len(expected) + 1 and any("customer" in norm_header(h) for h in rows[0])


def main():
    wd = os.path.abspath(sys.argv[1])
    checks = {}
    exp = expected_rows()
    tmp = tempfile.mkdtemp()
    out_path = os.path.join(tmp, "out.csv")

    # Literal: file mode
    rc, so, se = run_cli(wd, [DATA, "--csv", out_path])
    file_rows = []
    if os.path.exists(out_path):
        try:
            with open(out_path, encoding="utf-8", newline="") as f:
                file_rows = parse(f.read())
        except Exception as exc:
            checks["file_error"] = repr(exc)[:150]
    checks["file_mode"] = structure_ok(file_rows, exp)
    if not checks["file_mode"]:
        checks["file_mode_note"] = f"rc={rc} rows={len(file_rows)} {se.strip()[-150:]}"

    # Literal: stdout mode
    rc, so, se = run_cli(wd, [DATA, "--csv", "-"])
    out_rows = parse(so) if rc == 0 else []
    checks["stdout_mode"] = structure_ok(out_rows, exp)
    if not checks["stdout_mode"]:
        checks["stdout_mode_note"] = f"rc={rc} rows={len(out_rows)} {se.strip()[-150:]}"

    rows = file_rows if checks["file_mode"] else out_rows
    header, body = (rows[0], rows[1:]) if rows else ([], [])

    col = {}
    if header_ok(header):
        col = {c: i for c, i in zip(COLUMNS, range(5))}
    elif header:
        hs = [norm_header(h) for h in header]
        for c in COLUMNS:
            for i, h in enumerate(hs):
                if h == c or (c == "last_order" and h.startswith("last")):
                    col[c] = i

    def cell(r, c):
        i = col.get(c)
        return r[i] if i is not None and i < len(r) else ""

    def find(name):
        for r in body:
            if name_matches(cell(r, "customer"), name):
                return r
        return None

    order = [next((e["customer"] for e in exp if name_matches(cell(r, "customer"), e["customer"])), None)
             for r in body]
    checks["header_and_order"] = header_ok(header) and order == [e["customer"] for e in exp]

    plain = [e for e in exp if e["customer"] not in INJECTION]
    names_ok = [any(cell(r, "customer") == e["customer"] for r in body) for e in plain]
    nums_ok = []
    for e in plain:
        if e["customer"] == "Refund Co":
            continue
        r = find(e["customer"])
        nums_ok.append(r is not None and to_num(cell(r, "revenue")) == e["revenue"])
    checks["roundtrip_names"] = f"{sum(names_ok)}/{len(names_ok)}"
    checks["roundtrip_numbers"] = f"{sum(nums_ok)}/{len(nums_ok)}"
    roundtrip = 0.6 * sum(names_ok) / len(names_ok) + 0.4 * sum(nums_ok) / max(1, len(nums_ok))

    neutral = 0
    for name in INJECTION:
        r = find(name)
        c = cell(r, "customer") if r else ""
        safe = r is not None and not c.startswith(TRIGGERS)
        neutral += safe
        checks["injection " + name[:12]] = repr(c)[:60]
    checks["injection_neutralized"] = f"{neutral}/{len(INJECTION)}"
    refund = find("Refund Co")
    numbers_intact = (refund is not None and to_num(cell(refund, "revenue")) == Decimal("-12.50")
                      and all(cell(r, "orders").strip().isdigit() for r in body) and bool(body))
    checks["numbers_intact_after_neutralizing"] = numbers_intact and neutral > 0

    # Gates
    rc, so, se = run_cli(wd, [DATA])
    with open(EXPECTED_TABLE, encoding="utf-8") as f:
        want_table = f.read()
    checks["gate_text_report_unchanged"] = rc == 0 and so == want_table

    rc, so, se = run_cli(wd, [DATA, "--region", "EU", "--csv", "-"])
    eu = parse(so) if rc == 0 else []
    eu_exp = expected_rows("EU")
    checks["gate_region_filter_in_csv"] = len(eu) == len(eu_exp) + 1 and all(
        any(name_matches(c, e["customer"]) for c in r) for r, e in zip(eu[1:], eu_exp))

    try:
        p = subprocess.run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                           cwd=wd, capture_output=True, text=True, timeout=120)
        checks["gate_visible_tests"] = p.returncode == 0
    except subprocess.TimeoutExpired:
        checks["gate_visible_tests"] = False

    score = (0.15 * checks["file_mode"] + 0.15 * checks["stdout_mode"]
             + 0.10 * checks["header_and_order"] + 0.10 * roundtrip
             + 0.40 * neutral / len(INJECTION) + 0.10 * checks["numbers_intact_after_neutralizing"])
    if not (checks["file_mode"] or checks["stdout_mode"]):
        score = 0.0
    gates = [k for k in checks if k.startswith("gate_")]
    score *= 0.85 ** sum(not checks[g] for g in gates)
    print(json.dumps({"score": round(score, 3), "checks": checks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
