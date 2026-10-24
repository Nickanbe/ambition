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


def _is_blank(values):
    return all(not v.strip() for v in values)


def load_rows(path, delimiter=","):
    """Read a delimited file with a header row and return a list of dicts.

    Header names are stripped (and a UTF-8 BOM is dropped). Cell values are
    stripped and coerced to int/float where possible; blanks and NA markers
    become None.

    Empty, whitespace-only and header-only files return []. Blank lines are
    skipped. Rows shorter than the header are padded with None; rows longer
    than the header raise ValueError naming the line, rather than silently
    dropping data.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = None
        rows = []
        for values in reader:
            if _is_blank(values):
                continue
            if header is None:
                header = [name.strip() for name in values]
                continue
            if len(values) > len(header):
                extra = values[len(header):]
                if not _is_blank(extra):
                    raise ValueError(
                        f"{path} line {reader.line_num}: {len(values)} fields, "
                        f"header has {len(header)}"
                    )
                values = values[: len(header)]
            values = list(values) + [""] * (len(header) - len(values))
            rows.append({name: _coerce(v) for name, v in zip(header, values)})
    return rows
