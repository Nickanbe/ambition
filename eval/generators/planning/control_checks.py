

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
