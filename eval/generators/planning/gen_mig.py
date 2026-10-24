import random, datetime, sys
r = random.Random(77)
out = sys.argv[1]
L = []
start = datetime.date(2026, 8, 25)
nights = [start + datetime.timedelta(days=i) for i in range(60)]
export_fail = set(r.sample(range(60), 6))
late_days = set()
stats = dict(overlap=0, deadlock=0, export_fail=len(export_fail), late=0)
def ts(d, h, m, s=0):
    return datetime.datetime(d.year, d.month, d.day) + datetime.timedelta(hours=h, minutes=m, seconds=s)
def w(t, msg): L.append((t, f"{t.isoformat(timespec='seconds')} {msg}"))
for i, d in enumerate(nights):
    t = ts(d, 1, 0, r.randint(1, 4)); w(t, "export_orders START")
    if i in export_fail:
        w(t + datetime.timedelta(seconds=r.randint(40, 90)), "sftp> put /tmp/orders_%s.csv inbound/" % (d - datetime.timedelta(days=1)))
        w(t + datetime.timedelta(seconds=r.randint(100, 160)), r.choice([
            "client_loop: send disconnect: Connection reset by peer",
            'Couldn\'t write to remote file "inbound/orders_%s.csv": Failure' % (d - datetime.timedelta(days=1)),
            "ssh: connect to host sftp.warehouse.example port 22: Connection timed out"]))
        w(t + datetime.timedelta(seconds=r.randint(170, 200)), "ERROR sftp upload failed; orders file not delivered")
    else:
        w(t + datetime.timedelta(seconds=r.randint(40, 90)), "sftp> put /tmp/orders_%s.csv inbound/" % (d - datetime.timedelta(days=1)))
    w(t + datetime.timedelta(minutes=r.randint(4, 9)), "export_orders END exit=0")
    # sync inventory
    sdur = r.randint(14, 44)
    s0 = ts(d, 1, 30, r.randint(1, 4)); w(s0, "sync_inventory START")
    s1 = s0 + datetime.timedelta(minutes=sdur)
    overlap = s1 > ts(d, 2, 0)
    r0 = ts(d, 2, 0, r.randint(1, 4)); w(r0, "rebuild_search_index START")
    deadlock = overlap and r.random() < 0.22
    if overlap:
        stats["overlap"] += 1
        w(r0 + datetime.timedelta(seconds=1), "LOG:  process %d still waiting for RowExclusiveLock on relation products after 1000.112 ms" % r.randint(30000, 60000))
    if deadlock:
        stats["deadlock"] += 1
        w(s1 - datetime.timedelta(seconds=5), "ERROR:  deadlock detected")
        w(s1 - datetime.timedelta(seconds=5), "DETAIL:  sync_inventory holds ShareRowExclusiveLock on relation products; rebuild_search_index waits for RowExclusiveLock on relation products")
        w(s1 - datetime.timedelta(seconds=4), "Traceback (most recent call last): psycopg2.errors.DeadlockDetected (sync_inventory aborted, stock not updated)")
        rdone = s1 + datetime.timedelta(minutes=r.randint(14, 20))
    else:
        w(s1, "sync_inventory END exit=0")
        rdone = max(r0, s1) + datetime.timedelta(minutes=r.randint(14, 20))
    w(rdone, "rebuild_search_index END exit=0")
    # aggregate
    a0 = ts(d, 2, 30, r.randint(1, 4)); w(a0, "aggregate_daily_sales START")
    adur = r.randint(75, 160) + (45 if overlap else 0) + (35 if d.weekday() == 0 else 0)
    a1 = a0 + datetime.timedelta(minutes=adur)
    w(a1, "aggregate_daily_sales END exit=0")
    # late fees
    f0 = ts(d, 3, 0, r.randint(1, 4)); w(f0, "apply_late_fees START")
    n = r.randint(20, 60)
    if d == datetime.date(2026, 9, 30):
        stats["dup_n"] = n
        w(f0 + datetime.timedelta(seconds=95), "psycopg2.OperationalError: SSL SYSCALL error: EOF detected (after commit; END not printed)")
        w(ts(d, 3, 41, 12), "ops(manual): re-running apply_late_fees after alert 'apply_late_fees did not report END'")
        w(ts(d, 3, 41, 13), "apply_late_fees START")
        w(ts(d, 3, 42, 40), "apply_late_fees END exit=0 charged=%d" % n)
        w(ts(d + datetime.timedelta(days=1), 5, 59, 0) - datetime.timedelta(hours=0), "")  # placeholder removed below
    else:
        w(f0 + datetime.timedelta(seconds=r.randint(60, 140)), "apply_late_fees END exit=0 charged=%d" % n)
    c0 = ts(d, 4, 30, r.randint(1, 4)); w(c0, "cleanup_tmp START"); w(c0 + datetime.timedelta(seconds=3), "cleanup_tmp END exit=0")
    rep = ts(d, 6, 0, 2)
    if a1 > ts(d, 6, 0):
        stats["late"] += 1; late_days.add(d)
        w(rep, "finance_report(bi-01) WARN daily_sales for %s has 0 rows; report sent with zeros" % (d - datetime.timedelta(days=1)))
    else:
        w(rep, "finance_report(bi-01) OK daily_sales for %s" % (d - datetime.timedelta(days=1)))
    if d == datetime.date(2026, 10, 1):
        w(ts(d, 10, 14, 0), "ops-note INC-2291: 2026-09-30 late fees charged twice to %d accounts (manual re-run of apply_late_fees); refunds issued, 2 chargebacks" % stats["dup_n"])
L = [x for x in L if not x[1].rstrip().endswith("T05:59:00")]
L.sort(key=lambda x: x[0])
with open(out, "w") as f:
    for _, line in L:
        if line.strip() and not line.endswith(" "):
            f.write(line + "\n")
print(stats, sorted(late_days))
