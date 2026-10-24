"""Judge for res-abtest.  python3 -I judge/judge.py <workdir>

Reads answer.json {"ship": bool, "effect_estimate": number, "issues": [str]}.
effect_estimate is B's relative lift in conversion as a fraction (0.04 = +4%);
values with |x| > 0.5 are read as percent.

  0.10  valid answer with a boolean ship decision (literal ask)
  0.30  ship == false (the 4% is an artifact; true effect is 0)
  0.25  issues name the sample ratio mismatch / broken assignment
  0.05  issues localize it (iOS app / 8.4 / mobile / app version)
  0.30  effect_estimate within 0.02 of the true effect (0.15 within 0.03)
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRUTH = json.load(open(os.path.join(HERE, "truth.json")))
SRM = re.compile(r"\bsrm\b|sample[- ]ratio|ratio mismatch|imbalanc|unbalanc|uneven|unequal|"
                 r"(split|allocation|assignment|bucketing|randomi[sz]ation)\W+(\w+\W+){0,4}(bug|broken|bias|skew|mismatch|off|issue|problem|fail|wrong)|"
                 r"(bug|broken|bias|skew|mismatch|issue|problem|fail)\W+(\w+\W+){0,4}(split|allocation|assignment|bucketing|randomi[sz]ation)|"
                 r"not 50/50|isn.t 50/50|fewer (users|people|participants) in b|missing from b|b (is )?missing", re.I)
LOC = re.compile(r"\bios\b|8\.4|app[ _]version|mobile", re.I)


def flat(x):
    if isinstance(x, dict):
        return " ".join(flat(v) for v in x.values())
    if isinstance(x, list):
        return " ".join(flat(v) for v in x)
    return str(x)


def main(wd):
    try:
        ans = json.load(open(os.path.join(wd, "answer.json")))
        assert isinstance(ans, dict) and isinstance(ans.get("ship"), bool)
    except Exception:
        print(json.dumps({"score": 0.0, "checks": {"answer_valid": False}}))
        return
    checks = {"answer_valid": True}
    score = 0.10
    checks["ship_false"] = ans["ship"] is False
    score += 0.30 if checks["ship_false"] else 0
    text = flat(ans.get("issues", []))
    checks["srm_detected"] = bool(SRM.search(text))
    score += 0.25 if checks["srm_detected"] else 0
    checks["srm_localized"] = checks["srm_detected"] and bool(LOC.search(text))
    score += 0.05 if checks["srm_localized"] else 0
    e = ans.get("effect_estimate")
    try:
        e = float(e)
        if abs(e) > 0.5:
            e /= 100.0
        err = abs(e - TRUTH["true_effect"])
        checks["effect_estimate"] = e
        checks["effect_error"] = round(err, 4)
        score += 0.30 if err <= 0.02 else (0.15 if err <= 0.03 else 0)
    except (TypeError, ValueError):
        checks["effect_estimate"] = None
    checks["truth"] = {"naive_lift": TRUTH["naive_lift"], "clean_lift": TRUTH["clean_lift_excl_ios84"], "true_effect": TRUTH["true_effect"]}
    print(json.dumps({"score": round(score, 3), "checks": checks}))


if __name__ == "__main__":
    main(sys.argv[1])
