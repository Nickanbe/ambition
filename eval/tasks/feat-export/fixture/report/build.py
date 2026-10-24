"""Aggregate orders into one row per customer."""

from decimal import Decimal

COLUMNS = ["customer", "region", "orders", "revenue", "last_order"]


def build_report(orders, since=None, region=None):
    """Rows of {customer, region, orders, revenue, last_order}, biggest revenue first.

    since: only count orders on or after this date. region: exact region match.
    """
    by_customer = {}
    for o in orders:
        if since and o["date"] < since:
            continue
        if region and o["region"] != region:
            continue
        row = by_customer.setdefault(o["customer"], {
            "customer": o["customer"], "region": o["region"],
            "orders": 0, "revenue": Decimal("0"), "last_order": o["date"],
        })
        row["orders"] += 1
        row["revenue"] += o["amount"]
        row["last_order"] = max(row["last_order"], o["date"])
    return sorted(by_customer.values(), key=lambda r: (-r["revenue"], r["customer"]))
