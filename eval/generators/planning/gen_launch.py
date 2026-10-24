import csv, random, datetime, sys
r = random.Random(2025)
out = sys.argv[1]
today = datetime.date(2026, 10, 1)
EU = ["DE", "FR", "NL", "ES", "IE", "IT", "SE", "PL"]
rows = []
stats = {}
for i in range(2400):
    cid = "C%05d" % (10001 + i)
    plan = r.choices(["Starter", "Pro", "Team"], [0.25, 0.62, 0.13])[0]
    reg = r.choices(["US", "EU", "UK", "APAC"], [0.48, 0.27, 0.11, 0.14])[0]
    country = {"US": "US", "EU": r.choice(EU), "UK": "GB", "APAC": r.choice(["AU", "SG", "JP", "IN"])}[reg]
    tenure = r.choices([0, 1, r.randint(2, 3), r.randint(4, 12), r.randint(13, 48)], [0.07, 0.06, 0.12, 0.33, 0.42])[0]
    signup = today - datetime.timedelta(days=30 * tenure + r.randint(0, 29))
    billing = "monthly"
    cstart = cend = locked = ""
    if plan in ("Pro", "Team") and tenure >= 2 and r.random() < 0.2:
        billing = "annual"
        cstart_d = signup + datetime.timedelta(days=365 * ((today - signup).days // 365))
        cend_d = cstart_d + datetime.timedelta(days=365)
        cstart, cend = cstart_d.isoformat(), cend_d.isoformat()
        locked = cend
    seats = 1 if plan == "Starter" else (r.choices([1, 2, 3, 4, 5], [0.38, 0.25, 0.17, 0.12, 0.08])[0] if plan == "Pro" else r.randint(6, 40))
    integ = 0 if plan == "Starter" else (0 if (seats == 1 and r.random() < 0.55) else r.randint(0, 6))
    heavy = plan == "Pro" and seats == 1 and integ == 0 and r.random() < 0.55
    usage = int(r.lognormvariate(9.2, 0.6)) if not heavy else int(r.uniform(38000, 120000))
    price = {"Starter": 12, "Pro": 20, "Team": 49}[plan] * (seats if plan == "Team" else 1)
    if billing == "annual":
        price = price * 10  # 2 months free
    rows.append(dict(customer_id=cid, plan=plan, billing_cycle=billing, price_usd=price, signup_date=signup.isoformat(),
                     tenure_months=tenure, region=reg, country=country, seats=seats, integrations_used=integ,
                     monthly_usage_events=usage, contract_start=cstart, contract_end=cend, price_locked_until=locked))
with open(out + "/customers.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
pro = [x for x in rows if x["plan"] == "Pro"]
stats["pro"] = len(pro)
stats["pro_annual_locked"] = sum(1 for x in pro if x["billing_cycle"] == "annual")
stats["pro_eu"] = sum(1 for x in pro if x["region"] == "EU")
stats["pro_heavy_1seat_noint"] = sum(1 for x in pro if x["seats"] == 1 and x["integrations_used"] == 0 and x["monthly_usage_events"] >= 38000)
stats["pro_1seat_noint"] = sum(1 for x in pro if x["seats"] == 1 and x["integrations_used"] == 0)
stats["pro_tenure_le1"] = sum(1 for x in pro if x["tenure_months"] <= 1)
stats["pro_monthly"] = sum(1 for x in pro if x["billing_cycle"] == "monthly")
print(stats)
