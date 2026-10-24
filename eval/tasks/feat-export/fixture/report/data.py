"""Read the orders export (CSV: order_id, customer, region, amount, date)."""

import csv
import datetime
from decimal import Decimal


def load_orders(path):
    orders = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            orders.append({
                "order_id": row["order_id"],
                "customer": row["customer"],
                "region": row["region"],
                "amount": Decimal(row["amount"]),
                "date": datetime.date.fromisoformat(row["date"]),
            })
    return orders
