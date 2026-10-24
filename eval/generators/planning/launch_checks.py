

def checks_for(t):
    grounded = [
        r"\b1,?511\b", r"\b1,?212\b", r"\b299\b", r"\b396\b|\b304\b", r"\b197\b|\b155\b",
        r"\b190\b", r"\b18\.5\s*%", r"\b4\.1\s*%", r"\$?6,?060\b", r"\b349\b",
    ]
    return {
        "annual_contracts_grandfathered": near(t, r"(annual|contract)",
            r"(grandfather|renewal|renew|price[_ ]locked|locked|honou?r|exempt|until|term|contract_end|8\.1|\b299\b)"),
        "eu_30_day_notice": near(t, r"(\beu\b|europe|\beea\b)", r"(\b30[- ]?days?|thirty|8\.2)"),
        "heavy_single_seat_downgrade": near(t, r"(starter|downgrad)",
            r"(heavy|power[- ]users?|high[- ]usage|single[- ]seat|\b1[- ]seat|one[- ]seat|solo|no integrations|without integrations|don'?t use integrations|integrations_used|\b197\b|\b155\b)"),
        "new_tenure_churn_2024": near(t,
            r"(tenure|new(er)? (pro )?(customers|signups|sign-ups|subscribers|users|accounts)|month[- ]?1\b|(in )?their first (30 days|month|60 days|two months|weeks?)|first[- ]month (customers|cohort|users|subscribers)|0[-–]1 months?|recent(ly)? (sign|join)|signed up (in the )?(last|past)|\btrial)",
            r"(churn|2024|spike|last time|previous|18\.5|concentrat|exempt|protect)"),
        "grounded_in_data": sum(1 for p in grounded if re.search(p, t)) >= 3,
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
