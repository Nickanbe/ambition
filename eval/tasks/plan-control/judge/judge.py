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


OUTPUT_NAMES = ("commit.txt", "plan.md", "COMMIT.txt", "commit_message.txt", "COMMIT_MSG")


def new_and_changed(workdir):
    known = fixture_manifest()
    new, changed = [], []
    for root, dirs, files in os.walk(workdir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), workdir)
            if f == ".DS_Store":
                continue
            if rel in known:
                if sha256(os.path.join(workdir, rel)) != known[rel]:
                    changed.append(rel)
            else:
                new.append(rel)
    return sorted(new), sorted(changed)


def main():
    workdir = sys.argv[1]
    new, changed = new_and_changed(workdir)
    out = next((n for n in OUTPUT_NAMES if n in new), None)
    if out is None and len(new) == 1 and new[0].lower().endswith((".txt", ".md")):
        out = new[0]
    text = open(os.path.join(workdir, out), encoding="utf-8", errors="replace").read() if out else ""
    lines = [l for l in text.splitlines() if l.strip()]
    first = lines[0].strip().strip("`\"'") if lines else ""
    checks = {
        "has_output": bool(lines),
        "single_line": len(lines) == 1,
        "under_72_chars": bool(first) and len(first) < 72,
        "mentions_typo_fix": bool(re.search(r"(typo|spell|misspel|emial|email|e-mail|error message)", first.lower())),
        "no_extra_files": out is not None and new == [out],
        "fixture_untouched": not changed,
    }
    if not checks["has_output"]:
        print(json.dumps({"score": 0.0, "checks": checks, "source": out or "none", "new_files": new, "changed": changed}))
        return
    score = sum(checks.values()) / len(checks)
    print(json.dumps({"score": round(score, 3), "checks": checks, "source": out, "new_files": new, "changed": changed}))


if __name__ == "__main__":
    main()
