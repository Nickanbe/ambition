"""Load delimited text files (CSV exports from the billing system) into dicts."""

import csv

NULL_MARKERS = {"", "NA", "N/A", "null", "NULL"}


def _coerce(value):
    """Strip a raw cell and turn it into int, float, None or str."""
    value = value.strip()
    if value in NULL_MARKERS:
        return None
    for cast in (int, float):
        try:
            return cast(value)
        except ValueError:
            pass
    return value


def load_rows(path, delimiter=","):
    """Read a delimited file with a header row and return a list of dicts.

    Header names are stripped. Cell values are stripped and coerced to
    int/float where possible; blanks and NA markers become None.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = [name.strip() for name in next(reader)]
        rows = []
        for values in reader:
            rows.append({header[i]: _coerce(values[i]) for i in range(len(header))})
    return rows
