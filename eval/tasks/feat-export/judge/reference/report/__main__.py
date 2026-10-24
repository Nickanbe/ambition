"""python -m report ORDERS.csv [--since YYYY-MM-DD] [--region EU] [--csv FILE|-]"""

import argparse
import datetime
import sys

from .build import build_report
from .data import load_orders
from .export import write_csv
from .render import render_table


def main(argv=None):
    parser = argparse.ArgumentParser(prog="report", description="Revenue by customer.")
    parser.add_argument("orders", help="orders export CSV")
    parser.add_argument("--since", type=datetime.date.fromisoformat, help="only orders on/after this date")
    parser.add_argument("--region", help="only this region, e.g. EU")
    parser.add_argument("--csv", metavar="FILE", help="export the report as CSV to FILE ('-' for stdout)")
    args = parser.parse_args(argv)

    rows = build_report(load_orders(args.orders), since=args.since, region=args.region)
    if args.csv is None:
        print(render_table(rows))
    elif args.csv == "-":
        write_csv(rows, sys.stdout)
    else:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            write_csv(rows, f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
