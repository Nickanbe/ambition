import json, os, shutil, subprocess, sys, tempfile
TASKS = "/Users/nicholasbeaird/Code/ambition/eval/tasks"
SCR = "/private/tmp/claude-501/-Users-nicholasbeaird/6b4d2056-9278-451f-b4bf-0f71c73093b5/scratchpad/val"
os.makedirs(SCR, exist_ok=True)
for tid in ["plan-ci", "plan-migration", "plan-launch", "plan-control"]:
    res = {}
    for arm in ["untouched", "reference", "reference_generic"]:
        wd = tempfile.mkdtemp(dir=SCR, prefix=tid + "-" + arm + "-")
        shutil.rmtree(wd)
        shutil.copytree(os.path.join(TASKS, tid, "fixture"), wd)
        if arm != "untouched":
            shutil.copytree(os.path.join(TASKS, tid, "judge", arm), wd, dirs_exist_ok=True)
        out = subprocess.run([sys.executable, "-I", os.path.join(TASKS, tid, "judge", "judge.py"), wd], capture_output=True, text=True)
        res[arm] = json.loads(out.stdout)["score"] if out.returncode == 0 else ("ERR " + out.stderr[-300:])
        shutil.rmtree(wd)
    print(tid, res)
