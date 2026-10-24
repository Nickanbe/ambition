#!/usr/bin/env python3
"""Roll up yesterday's orders into daily_sales.

finance_report (BI team, 06:00 sharp) emails the CFO from daily_sales.
If this has not finished by then the report goes out with zeros.
"""
import datetime, psycopg2

print(f"{datetime.datetime.now().isoformat()} aggregate_daily_sales START", flush=True)
conn = psycopg2.connect("dbname=shopdb")
cur = conn.cursor()
day = datetime.date.today() - datetime.timedelta(days=1)
cur.execute("DELETE FROM daily_sales WHERE day = %s", (day,))
cur.execute("""
    INSERT INTO daily_sales (day, sku, units, revenue)
    SELECT %s, oi.sku, sum(oi.qty), sum(oi.qty * p.price)
    FROM order_items oi JOIN orders o ON o.id = oi.order_id JOIN products p ON p.sku = oi.sku
    WHERE o.created_at::date = %s GROUP BY oi.sku
""", (day, day))
conn.commit()
print(f"{datetime.datetime.now().isoformat()} aggregate_daily_sales END exit=0", flush=True)
