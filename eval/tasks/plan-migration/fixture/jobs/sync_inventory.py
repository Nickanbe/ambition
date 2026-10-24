#!/usr/bin/env python3
"""Pull stock levels from the supplier API and update products.stock."""
import datetime, psycopg2, requests

print(f"{datetime.datetime.now().isoformat()} sync_inventory START", flush=True)
conn = psycopg2.connect("dbname=shopdb")
cur = conn.cursor()
cur.execute("LOCK TABLE products IN SHARE ROW EXCLUSIVE MODE")  # avoid partial stock views
for page in range(1, 400):
    items = requests.get(f"https://supplier.example/api/stock?page={page}", timeout=30).json()
    if not items:
        break
    for it in items:
        cur.execute("UPDATE products SET stock = %s, stock_synced_at = now() WHERE sku = %s", (it["qty"], it["sku"]))
conn.commit()
print(f"{datetime.datetime.now().isoformat()} sync_inventory END exit=0", flush=True)
