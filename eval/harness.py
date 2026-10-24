"""Ambition eval harness. See SPEC.md.

    python3 -I eval/harness.py prep <run_id>    copy each fixture into runs/<run_id>/<task>/{A,B}
    python3 -I eval/harness.py score <run_id>   run every judge, write results.json and summary.md
    python3 -I eval/harness.py blind <run_id>   shuffle human-judged plans into blind/ as X/Y

Arms are executed by agents outside this script; each writes only inside its own arm directory.
B's skill output goes to runs/<run_id>/<task>/ambition.md, beside the arm directories.
"""
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys

EVAL = pathlib.Path(__file__).resolve().parent
TASKS = EVAL / "tasks"
# Keep arm directories away from the repo so arms can't wander into judge/.
RUNS = pathlib.Path(os.environ.get("AMBITION_RUNS", EVAL / "runs"))
ARMS = ("A", "B")


def tasks():
    for d in sorted(TASKS.iterdir()):
        if (d / "task.json").exists():
            yield d, json.loads((d / "task.json").read_text())


def prep(run_id):
    for d, t in tasks():
        for arm in ARMS:
            dest = RUNS / run_id / t["id"] / arm
            if dest.exists():
                sys.exit(f"{dest} exists; pick a new run id")
            shutil.copytree(d / "fixture", dest)
    print(RUNS / run_id)


def judge(task_dir, workdir):
    out = subprocess.run(
        [sys.executable, "-I", str(task_dir / "judge" / "judge.py"), str(workdir)],
        capture_output=True, text=True, timeout=600,
    )
    lines = [l for l in out.stdout.splitlines() if l.strip().startswith("{")]
    if out.returncode or not lines:
        return {"score": None, "error": (out.stderr or out.stdout)[-500:]}
    return json.loads(lines[-1])


def score(run_id):
    root = RUNS / run_id
    results, rows = {}, []
    for d, t in tasks():
        r = {arm: judge(d, root / t["id"] / arm) for arm in ARMS}
        a, b = r["A"].get("score"), r["B"].get("score")
        delta = None if a is None or b is None else round(b - a, 3)
        results[t["id"]] = {"mode": t["mode"], "control": t.get("control", False), "judge": t["judge"], **r, "delta": delta}
        rows.append(f"| {t['id']} | {t['mode']}{' (control)' if t.get('control') else ''} | {a} | {b} | {delta} |")
    (root / "results.json").write_text(json.dumps(results, indent=2))
    wins = sum(1 for v in results.values() if v["delta"] is not None and v["delta"] > 0)
    ties = sum(1 for v in results.values() if v["delta"] == 0)
    summary = ["| Task | Mode | A | B | B - A |", "|---|---|---|---|---|", *rows, "",
               f"B wins {wins}, ties {ties}, of {len(results)} (auto scores only; human ranks in blind/)"]
    (root / "summary.md").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


def blind(run_id):
    root = RUNS / run_id
    out = root / "blind"
    out.mkdir(exist_ok=True)
    key = {}
    rng = random.SystemRandom()
    for d, t in tasks():
        if t["judge"] != "human":
            continue
        arms = list(ARMS)
        rng.shuffle(arms)
        key[t["id"]] = dict(zip("XY", arms))
        for label, arm in key[t["id"]].items():
            src = root / t["id"] / arm / "plan.md"
            dst = out / f"{t['id']}-{label}.md"
            dst.write_text(src.read_text() if src.exists() else "(no plan.md written)\n")
        shutil.copy(d / "judge" / "rubric.md", out / f"{t['id']}-rubric.md")
    (root / "blind-key.json").write_text(json.dumps(key, indent=2))
    print(out)


if __name__ == "__main__":
    cmd, run_id = sys.argv[1], sys.argv[2]
    {"prep": prep, "score": score, "blind": blind}[cmd](run_id)
