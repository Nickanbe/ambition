"""CSV export of the report rows.

Raw values, not the terminal formatting: full names (no truncation), plain
numbers (no $ or thousands separators), ISO dates. Text cells that a
spreadsheet would treat as a formula (starting with = + - @ tab or CR) are
prefixed with a single quote (OWASP CSV injection guidance). Numbers are
written as numbers, so a refund stays -12.50.
"""

import csv
import datetime
from decimal import Decimal

from .build import COLUMNS

FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def _cell(value):
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, datetime.date):
        return value.isoformat()
    text = "" if value is None else str(value)
    if text.startswith(FORMULA_TRIGGERS):
        return "'" + text
    return text


def write_csv(rows, fp):
    writer = csv.writer(fp, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for r in rows:
        writer.writerow([_cell(r[c]) for c in COLUMNS])
