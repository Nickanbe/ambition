# res-control reference

`python3 -c "import csv; print(sum(float(r['amount_usd']) > 100 for r in csv.DictReader(open('orders.csv'))))"` -> 78.
8 orders are exactly 100.00 and are not "over $100" (>= 100 gives 86). Nothing else is needed.
