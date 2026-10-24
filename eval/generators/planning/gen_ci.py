import csv, random, datetime, hashlib, sys
out = sys.argv[1]
r = random.Random(4242)
rows, flaky = [], []
t = datetime.datetime(2026, 9, 1, 9, 0)
run_id = 81000
docker_shas = ["9f2c1ab", "9f2c1ab", "d41e07c", "d41e07c", "d41e07c"]
commits = 0
real_fail_at = set(r.sample(range(174), 6))
rerun_at = set(r.sample([i for i in range(174) if i not in real_fail_at], 26))
dsha = "9f2c1ab"
for c in range(174):
    if c == 61: dsha = "d41e07c"
    if c == 133: dsha = "77b0e5a"
    sha = hashlib.sha1(str(c).encode()).hexdigest()[:7]
    branch = "main" if r.random() < 0.3 else "feature/" + r.choice(["billing", "search", "auth", "ui", "deps", "api"]) + "-" + str(r.randint(10, 99))
    t += datetime.timedelta(minutes=r.randint(40, 300))
    attempts = [1, 2] if c in rerun_at else [1]
    for a in attempts:
        run_id += 1
        st = t + datetime.timedelta(minutes=0 if a == 1 else 41)
        d = dict(
            checkout_s=r.randint(18, 34),
            install_deps_s=int(r.gauss(372, 28)),
            docker_build_s=int(r.gauss(418, 35)),
            unit_shard_1_s=int(r.gauss(241, 18)),
            unit_shard_2_s=int(r.gauss(252, 20)),
            unit_shard_3_s=int(r.gauss(731, 45)),
            unit_shard_4_s=int(r.gauss(236, 17)),
            e2e_s=int(r.gauss(688, 52)),
        )
        overhead = r.randint(20, 45)
        wall = d["checkout_s"] + d["install_deps_s"] + d["docker_build_s"] + max(d[k] for k in d if k.startswith("unit")) + d["e2e_s"] + overhead
        conclusion, failed = "success", ""
        if c in rerun_at and a == 1:
            conclusion, failed = "failure", "tests/e2e/checkout/payment.spec.ts > applies coupon after price refresh"
            flaky.append((st + datetime.timedelta(seconds=wall - 40), run_id, a))
        elif c in real_fail_at:
            conclusion = "failure"
            failed = r.choice(["tests/unit/billing/proration.test.ts > rounds half-cents", "tests/integration/search/indexer.test.ts > reindexes deleted docs", "tests/unit/auth/session.test.ts > expires refresh token"])
        rows.append(dict(run_id=run_id, started_at=st.strftime("%Y-%m-%dT%H:%M:%SZ"), commit_sha=sha, branch=branch, attempt=a,
                         conclusion=conclusion, dockerfile_sha=dsha, deps_cache_hit="false", **d, total_wall_s=wall, failed_test=failed))
with open(out + "/ci_runs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
with open(out + "/flaky-tests.log", "w") as f:
    for ts, rid, a in flaky:
        f.write(f"{ts:%Y-%m-%dT%H:%M:%SZ} run={rid} attempt={a} job=e2e FAIL tests/e2e/checkout/payment.spec.ts:88:5 > applies coupon after price refresh\n")
        f.write(f"{ts:%Y-%m-%dT%H:%M:%SZ} run={rid}   TimeoutError: expect(locator('[data-test=order-total]')).toHaveText('$18.00') timed out after 5000ms; received '$20.00'\n")
        f.write(f"{ts:%Y-%m-%dT%H:%M:%SZ} run={rid}   note: price-refresh request still pending (GET /api/cart/reprice 200 in 5312ms)\n")
        f.write(f"{ts:%Y-%m-%dT%H:%M:%SZ} run={rid}   action: workflow re-run requested by author (Re-run failed jobs disabled: e2e needs build-image)\n")
print(len(rows), len(flaky))
