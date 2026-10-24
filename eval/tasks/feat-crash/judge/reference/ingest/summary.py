"""Quick numeric summaries over a loaded file."""

from .loader import load_rows


def summarize(path, field="amount", delimiter=","):
    """Return row count plus total/mean/max of one numeric column.

    mean and max are None when the column has no numeric values.
    """
    rows = load_rows(path, delimiter=delimiter)
    values = [r.get(field) for r in rows]
    values = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return {
        "rows": len(rows),
        "total": sum(values),
        "mean": sum(values) / len(values) if values else None,
        "max": max(values) if values else None,
    }
