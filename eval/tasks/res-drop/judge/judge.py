"""Judge for res-drop.  python3 -I judge/judge.py <workdir>

Score (max 1.0):
  0.10  answer.json present with a non-empty causes list (literal answer)
  0.30  names the Safari 19.3 tracking/instrumentation loss (0.12 if it names
        Safari 19.3 but treats it as a real loss of signups)
  0.15  tracking share within +/-0.15 of truth
  0.20  names the IN price increase
  0.10  price share within +/-0.12 of truth
  0.15  does not attribute >=10% of the drop to the seasonal paid_social dip
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRUTH = json.load(open(os.path.join(HERE, "truth.json")))

TRACK = re.compile(r"track|instrument|analytics (bug|issue|gap|loss|outage|pipeline)|telemetry|logging|not logged|unlogged|not recorded|unrecorded|"
                   r"not captured|missing event|events? (are |were )?(missing|lost|vanish)|event loss|"
                   r"under-?count|under-?report|measurement|reporting (bug|issue|gap)|data (loss|gap|pipeline)|"
                   r"not (a )?real (drop|decline|loss)|signups? (still )?(happened|occurred)", re.I)
SAFARI = re.compile(r"safari|19\.3", re.I)
PRICE = re.compile(r"pric", re.I)
INDIA = re.compile(r"(?i:india)|\bIN\b")
SOCIAL = re.compile(r"paid[_ ]social|social", re.I)


def flat(x):
    if isinstance(x, dict):
        return " ".join(flat(v) for v in x.values()) + " " + " ".join(map(str, x.keys()))
    if isinstance(x, list):
        return " ".join(flat(v) for v in x)
    return str(x)


def share(c):
    for k in ("share_of_drop", "share", "fraction", "pct", "percent"):
        if k in c:
            try:
                v = float(c[k])
                return v / 100.0 if v > 1.0 else v
            except (TypeError, ValueError):
                pass
    return None


def main(wd):
    checks = {}
    p = os.path.join(wd, "answer.json")
    try:
        ans = json.load(open(p))
        causes = ans.get("causes") if isinstance(ans, dict) else None
        causes = [c for c in causes if isinstance(c, dict)] if isinstance(causes, list) else []
    except Exception:
        causes = []
    if not causes:
        print(json.dumps({"score": 0.0, "checks": {"answer_present": False}}))
        return
    score = 0.10
    checks["answer_present"] = True
    track_c = price_c = None
    safari_only = False
    herring = False
    for c in causes:
        t = flat(c)
        is_track = bool(SAFARI.search(t) and TRACK.search(t))
        is_price = bool(PRICE.search(t) and INDIA.search(t))
        if is_track and track_c is None:
            track_c = c
        elif SAFARI.search(t) and not is_track:
            safari_only = True
        if is_price and price_c is None and c is not track_c:
            price_c = c
        s = share(c)
        if SOCIAL.search(t) and not is_track and not is_price and (s is None or s >= 0.10):
            herring = True
    if track_c is not None:
        score += 0.30
        s = share(track_c)
        ok = s is not None and abs(s - TRUTH["tracking_share"]) <= 0.15
        score += 0.15 if ok else 0
        checks["tracking_cause"] = True
        checks["tracking_share"] = s
        checks["tracking_share_ok"] = ok
    else:
        checks["tracking_cause"] = False
        if safari_only:
            score += 0.12
            checks["safari_segment_named_but_not_tracking"] = True
    if price_c is not None:
        score += 0.20
        s = share(price_c)
        ok = s is not None and abs(s - TRUTH["price_share"]) <= 0.12
        score += 0.10 if ok else 0
        checks["price_cause"] = True
        checks["price_share"] = s
        checks["price_share_ok"] = ok
    else:
        checks["price_cause"] = False
    checks["red_herring_claimed"] = herring
    if not herring:
        score += 0.15
    checks["truth"] = {k: TRUTH[k] for k in ("tracking_share", "price_share", "drop_pct")}
    print(json.dumps({"score": round(min(score, 1.0), 3), "checks": checks}))


if __name__ == "__main__":
    main(sys.argv[1])
