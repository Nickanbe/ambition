"""python -m report ORDERS.csv [--since YYYY-MM-DD] [--region EU]"""

import argparse
import csv
import datetime
import sys

from .build import build_report
from .data import load_orders
from .render import render_table


def main(argv=None):
    parser = argparse.ArgumentParser(prog="report", description="Revenue by customer.")
    parser.add_argument("orders", help="orders export CSV")
    parser.add_argument("--since", type=datetime.date.fromisoformat, help="only orders on/after this date")
    parser.add_argument("--region", help="only this region, e.g. EU")
    parser.add_argument("--csv", help="write CSV to this file, or - for stdout")
    args = parser.parse_args(argv)

    rows = build_report(load_orders(args.orders), since=args.since, region=args.region)
    if args.csv:
        f = sys.stdout if args.csv == "-" else open(args.csv, "w", newline="", encoding="utf-8")
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        w.writeheader()
        w.writerows(rows)
        if f is not sys.stdout:
            f.close()
    else:
        print(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
