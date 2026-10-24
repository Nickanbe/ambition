

MIN = r"\s*(min|mins|minutes|m)\b"


def checks_for(t):
    grounded_numbers = [
        r"\b6(\.[01]\d?)?" + MIN,            # install ~6.1 min
        r"\b(7|6\.9\d?|7\.0)" + MIN,         # docker ~7.0 min
        r"\b12(\.1\d?)?" + MIN,              # shard 3 ~12.1 min
        r"\b11(\.[45]\d?)?" + MIN,           # e2e ~11.5 min
        r"\b(15|14\.9)\s*%",                 # rerun rate
        r"\b4[23](\.\d+)?" + MIN,            # effective time per commit incl. reruns
        r"\b37(\.[67]\d?)?" + MIN,           # measured mean wall
    ]
    return {
        "shard_imbalance": near(t, r"shard",
            r"(shard[\s_#-]*3\b|unit_shard_3|\b3(\.\d)?\s*x\b|\bthree times|\b1[12](\.\d+)?" + MIN +
            r"|\b7[0-4]\d\s*s\b|tests/integration|integration (tests|suite|dir|directory))"),
        "deps_not_cached": near(t, r"(npm ci|node_modules|dependenc|\binstall)", r"cach")
            and near(t, r"(npm ci|node_modules|dependenc|\binstall)",
            r"(\b6(\.\d+)?" + MIN + r"|\b3[5-8]\d\s*s\b|deps_cache_hit|cache[_ -]hit|setup-node|package-lock|lockfile|never cached|no cache|not cached|uncached)"),
        "flaky_reruns": near(t, r"(flak|re-?run|retr|quarantin)",
            r"(payment\.spec|payment spec|coupon|price[- ]refresh|reprice|order-total|\b1[3-6](\.\d)?\s*%|\b26\s*(of|/|out of)\s*(174|200)|\b26 (re-?runs|runs|commits|of))"),
        "docker_rebuilt_unchanged": near(t, r"(docker|image)",
            r"(--no-cache|no-cache|dockerfile_sha|dockerfile (hash|sha|unchanged|changed|rarely|only)|unchanged|changed (only )?(twice|2 times|two times)|\b(3|three) distinct|only (when|if) (the )?dockerfile|\bpaths?:|path filter|\b(7|6\.9\d?|7\.0)" + MIN + r"|\b4[0-2]\d\s*s\b)"),
        "e2e_serial": near(t, r"(e2e|end-to-end|playwright)",
            r"(--workers[= ]1|workers[=: ]+1\b|one worker|single worker|\b1 worker|serial|fullyparallel|sequential|one at a time|\b11(\.\d+)?" + MIN + r"|\b6[5-9]\d\s*s\b)"),
        "target_with_measurement": bool(re.search(
            r"(target|goal|aim|budget|slo|down to|get (it )?to|under|below|<=|≤|<)[^\n]{0,60}?\b([1-9]|[12]\d)" + MIN, t))
            and bool(re.search(r"(p50|p90|p95|median|percentile|ci_runs|dashboard|weekly|re-?run rate|measure|tracked|track)", t)),
        "quantified_from_data": sum(1 for p in grounded_numbers if re.search(p, t)) >= 4,
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
