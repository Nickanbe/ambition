"""Command line: python -m ingest summary FILE [--field amount]
                python -m ingest head FILE [-n 5]"""

import argparse
import json

from .loader import load_rows
from .summary import summarize


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ingest")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sum = sub.add_parser("summary", help="row count and stats for one column")
    p_sum.add_argument("path")
    p_sum.add_argument("--field", default="amount")
    p_sum.add_argument("--delimiter", default=",")

    p_head = sub.add_parser("head", help="print the first rows as JSON")
    p_head.add_argument("path")
    p_head.add_argument("-n", type=int, default=5)
    p_head.add_argument("--delimiter", default=",")

    args = parser.parse_args(argv)
    if args.command == "summary":
        stats = summarize(args.path, field=args.field, delimiter=args.delimiter)
        for key, value in stats.items():
            print(f"{key:>6}: {value}")
    else:
        for row in load_rows(args.path, delimiter=args.delimiter)[: args.n]:
            print(json.dumps(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
