"""Quick numeric summaries over a loaded file."""

from .loader import load_rows


def summarize(path, field="amount", delimiter=","):
    """Return row count plus total/mean/max of one numeric column."""
    rows = load_rows(path, delimiter=delimiter)
    values = [r[field] for r in rows if r.get(field) is not None]
    return {
        "rows": len(rows),
        "total": sum(values),
        "mean": sum(values) / len(values),
        "max": max(values),
    }
