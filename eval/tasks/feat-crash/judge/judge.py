"""Judge for feat-crash.  Usage: python3 -I judge/judge.py <workdir>

Prints one JSON line {"score": 0..1, "checks": {...}}.

Score = 0.3 * literal (empty file loads to [])
      + 0.1 * each of 7 hardening checks (crash-free on related inputs)
      then x0.8 for each broken regression gate (visible tests, header-only,
      CRLF, over-long rows must not raise anything but ValueError).
"""

import json
import os
import subprocess
import sys
import tempfile

HARNESS = r'''
import json, os, re, sys, tempfile
sys.path.insert(0, sys.argv[1])
results = {}
try:
    from ingest import load_rows
except Exception as exc:
    print(json.dumps({"_import": repr(exc)}))
    raise SystemExit(0)
try:
    from ingest import summarize
except Exception:
    summarize = None

tmpdir = tempfile.mkdtemp()

def path_for(name, text):
    p = os.path.join(tmpdir, name + ".csv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return p

def check(name, fn):
    try:
        ok, note = fn()
    except Exception as exc:
        ok, note = False, "raised " + type(exc).__name__ + ": " + str(exc)[:120]
    results[name] = {"ok": bool(ok), "note": note}

def load(name, text):
    return load_rows(path_for(name, text))

def c_empty():
    r = load("empty", "")
    return r == [], repr(r)[:120]

def c_whitespace():
    r = load("ws", "   \n\n  \n")
    return r == [], repr(r)[:120]

def c_bom():
    r = load("bom", "﻿id,name,amount\n1,a,5\n")
    return len(r) == 1 and r[0].get("id") == 1 and r[0].get("amount") == 5, repr(r)[:120]

def c_trailing():
    r = load("trail", "id,name,amount\n1,a,5\n\n\n")
    return len(r) == 1 and r[0].get("amount") == 5, repr(r)[:120]

def c_blank_middle():
    r = load("mid", "id,name,amount\n1,a,5\n\n2,b,6\n")
    return [x.get("id") for x in r] == [1, 2], repr(r)[:120]

def c_ragged_short():
    try:
        r = load("short", "id,name,amount\n1,a,5\n2,b\n3,c,7\n")
    except ValueError as exc:
        nums = set(re.findall(r"\d+", str(exc)))
        return bool(nums & {"2", "3"}), "ValueError: " + str(exc)[:100]
    ok = (len(r) == 3 and r[1].get("id") == 2 and r[1].get("amount") in (None, "")
          and r[2].get("amount") == 7)
    return ok, repr(r)[:120]

def c_summary_empty():
    if summarize is None:
        return False, "no summarize"
    s = summarize(path_for("sumempty", ""))
    return s.get("rows") == 0, repr(s)[:120]

def g_header_only():
    r = load("hdr", "id,name,amount\n")
    return r == [], repr(r)[:120]

def g_crlf():
    r = load("crlf", "id,name,amount\r\n1,a,5\r\n2,b,6\r\n")
    ok = [(x.get("id"), x.get("name"), x.get("amount")) for x in r] == [(1, "a", 5), (2, "b", 6)]
    return ok, repr(r)[:120]

def g_ragged_long():
    try:
        r = load("long", "id,name\n1,a,EXTRA\n2,b\n")
    except ValueError as exc:
        return True, "ValueError: " + str(exc)[:100]
    return isinstance(r, list), repr(r)[:120]

for n, f in [("empty_file", c_empty), ("whitespace_only", c_whitespace), ("bom", c_bom),
             ("trailing_blank_lines", c_trailing), ("blank_line_mid_file", c_blank_middle),
             ("ragged_short_row", c_ragged_short), ("summarize_empty", c_summary_empty),
             ("gate_header_only", g_header_only), ("gate_crlf", g_crlf),
             ("gate_ragged_long_no_crash", g_ragged_long)]:
    check(n, f)
print(json.dumps(results))
'''

CREDIT = ["whitespace_only", "bom", "trailing_blank_lines", "blank_line_mid_file",
          "ragged_short_row", "summarize_empty", "cli_header_only"]
GATES = ["gate_visible_tests", "gate_header_only", "gate_crlf", "gate_ragged_long_no_crash"]


def run(args, cwd, timeout=60):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"


def main():
    wd = os.path.abspath(sys.argv[1])
    checks = {}

    code, out, err = run([sys.executable, "-I", "-B", "-c", HARNESS, wd], cwd=wd)
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except Exception:
        res = {"_harness": (err or out)[-300:]}
    for k, v in res.items():
        if isinstance(v, dict):
            checks[k] = v
        else:
            checks[k] = {"ok": False, "note": v}

    # CLI on a header-only file: the path a user actually runs.
    tmp = tempfile.mkdtemp()
    hdr = os.path.join(tmp, "header_only.csv")
    with open(hdr, "w", encoding="utf-8") as f:
        f.write("id,customer,amount\n")
    cli = ("import sys, runpy; sys.path.insert(0, sys.argv[1]); "
           "sys.argv = ['ingest', 'summary', sys.argv[2]]; "
           "runpy.run_module('ingest', run_name='__main__')")
    code, out, err = run([sys.executable, "-I", "-B", "-c", cli, wd, hdr], cwd=wd)
    checks["cli_header_only"] = {"ok": "Traceback" not in err and code != -1,
                                 "note": f"rc={code} {err.strip()[-120:]}"}

    code, out, err = run([sys.executable, "-I", "-B", "-m", "unittest", "discover",
                          "-s", "tests", "-t", "."], cwd=wd, timeout=120)
    checks["gate_visible_tests"] = {"ok": code == 0, "note": err.strip().splitlines()[-1] if err.strip() else ""}

    def ok(name):
        return bool(checks.get(name, {}).get("ok"))

    score = 0.3 * ok("empty_file") + 0.1 * sum(ok(c) for c in CREDIT)
    failed_gates = sum(not ok(g) for g in GATES)
    score *= 0.8 ** failed_gates
    flat = {k: v["ok"] if isinstance(v, dict) and "ok" in v else v for k, v in checks.items()}
    notes = {k: v.get("note") for k, v in checks.items() if isinstance(v, dict) and not v.get("ok")}
    print(json.dumps({"score": round(min(1.0, score), 3), "checks": flat, "failures": notes}))


if __name__ == "__main__":
    main()
