"""Plain-text table for the terminal."""

HEADERS = ["Customer", "Region", "Orders", "Revenue", "Last order"]
NAME_WIDTH = 22


def _short(text, width):
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def render_table(rows):
    cells = [[
        _short(r["customer"], NAME_WIDTH),
        r["region"],
        str(r["orders"]),
        "${:,.2f}".format(r["revenue"]),
        r["last_order"].strftime("%b %d, %Y"),
    ] for r in rows]
    widths = [max([len(h)] + [len(c[i]) for c in cells]) for i, h in enumerate(HEADERS)]
    right = {2, 3}

    def fmt(values):
        return "  ".join(v.rjust(w) if i in right else v.ljust(w)
                         for i, (v, w) in enumerate(zip(values, widths))).rstrip()

    lines = [fmt(HEADERS), "  ".join("-" * w for w in widths)]
    lines += [fmt(c) for c in cells]
    total = sum(r["revenue"] for r in rows)
    lines.append("")
    lines.append(f"{len(rows)} customers, ${total:,.2f} total")
    return "\n".join(lines)
