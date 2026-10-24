"""Build the site: render examples/*.md into the page, zip the skill, copy SKILL.md.

Run from anywhere: python3 -I scripts/build.py
Also refresh the nickbeaird.com project quick look (written into that repo's index.html):
    python3 -I scripts/build.py --quicklook ~/Code/personal-website/index.html
"""
import html
import pathlib
import re
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "ambition"
SITE = ROOT / "site" / "ambition"  # served at /ambition/, fonts at /fonts/

# Tab order and labels. The ask is the prompt each run was given.
RUNS = [
    ("feature", "A feature", "/ambition Add a CSV export button to the orders table in our admin dashboard. light"),
    ("research", "A research question", "/ambition Figure out why our newsletter's open rate dropped from 41% to 33% over the last two months. full"),
    ("planning", "A plan", "/ambition Plan the agenda for our 12-person engineering team's two-day offsite in January. light"),
]


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", text)
    return text


def table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    out = ['<div class="table-wrap"><table><thead><tr>']
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render(md):
    lines = md.strip().splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
            i += 1
        elif line.startswith("## "):
            title = re.sub(r"(\d{4}-\d{2}-\d{2})", r'<span class="date">\1</span>', inline(line[3:]))
            out.append(f"<h2>{title}</h2>")
            i += 1
        elif line.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(table(block))
        elif re.match(r"\s*[-*] ", line):
            items = []
            while i < len(lines) and (re.match(r"\s*[-*] ", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r"\s*[-*] ", lines[i]):
                    items.append(re.sub(r"^\s*[-*] ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(t)}</li>" for t in items) + "</ul>")
        elif re.match(r"\s*\d+\. ", line):
            items = []
            while i < len(lines) and (re.match(r"\s*\d+\. ", lines[i]) or (lines[i].startswith("   ") and lines[i].strip())):
                if re.match(r"\s*\d+\. ", lines[i]):
                    items.append(re.sub(r"^\s*\d+\. ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(t)}</li>" for t in items) + "</ol>")
        elif line.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i][1:].lstrip())
                i += 1
            out.append("<blockquote>" + render("\n".join(block)) + "</blockquote>")
        else:
            para = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"(#{2,3} |\s*\||\s*[-*] |\s*\d+\. |>)", lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{inline(' '.join(p.strip() for p in para))}</p>")
    return "\n".join(out)


def replace_between(page, name, content):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    a, b = page.index(start) + len(start), page.index(end)
    return page[:a] + "\n" + content + "\n" + page[b:]


def build_page():
    index = SITE / "index.html"
    page = index.read_text()
    tabs, panels = [], []
    for n, (slug, label, ask) in enumerate(RUNS):
        md = (ROOT / "examples" / f"{slug}.md").read_text()
        first = n == 0
        tabs.append(
            f'<button role="tab" id="tab-{slug}" aria-controls="run-{slug}" '
            f'aria-selected="{str(first).lower()}" tabindex="{0 if first else -1}" type="button">{label}</button>'
        )
        panels.append(
            f'<div class="run" role="tabpanel" id="run-{slug}" aria-labelledby="tab-{slug}"{"" if first else " hidden"}>'
            f'<p class="ask">{html.escape(ask)}</p><div class="out">{render(md)}</div></div>'
        )
    page = replace_between(page, "tabs", "\n".join(tabs))
    page = replace_between(page, "runs", "\n".join(panels))
    index.write_text(page)


def build_zip():
    target = SITE / "ambition.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SKILL_DIR.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                z.write(f, pathlib.Path("ambition") / f.relative_to(SKILL_DIR))
    (SITE / "SKILL.md").write_text((SKILL_DIR / "SKILL.md").read_text())


def check_frontmatter():
    """Catch frontmatter that lenient parsers accept but strict YAML (the skills CLI) rejects."""
    text = (SKILL_DIR / "SKILL.md").read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit("SKILL.md: missing frontmatter")
    fields = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(": ")
        if not sep:
            raise SystemExit(f"SKILL.md frontmatter: can't read line {line!r}")
        quoted = len(value) >= 2 and value[0] == value[-1] == '"'
        if not quoted and (": " in value or " #" in value or value[:1] in "&*!|>'\"%@`{[]"):
            raise SystemExit(f"SKILL.md frontmatter: quote the {key} value; strict YAML parsers reject it as written")
        fields[key] = value[1:-1] if quoted else value
    if fields.get("name") != SKILL_DIR.name:
        raise SystemExit("SKILL.md: name must match the folder name")
    if not 0 < len(fields.get("description", "")) <= 200:
        raise SystemExit("SKILL.md: description must be 1 to 200 characters (the Claude app limit)")


QUICKLOOK_START, QUICKLOOK_END = "/* ambition-quicklook:start */", "/* ambition-quicklook:end */"


def quicklook_diagram():
    """The page's diagram, recoloured with nickbeaird.com's tokens and given ids that can't clash there."""
    page = (SITE / "index.html").read_text()
    svg = page[page.index('<svg viewBox="0 0 600 380"'):page.index("</svg>", page.index('<svg viewBox="0 0 600 380"')) + len("</svg>")]
    for old, new in [("var(--ink-soft)", "var(--text-secondary)"), ("var(--ink)", "var(--text-primary)"),
                     ("var(--muted)", "var(--text-muted)"), ("var(--paper)", "var(--bg-primary)"),
                     ('id="arrow"', 'id="amb-arrow"'), ("url(#arrow)", "url(#amb-arrow)"),
                     ('id="compass-title"', 'id="amb-compass-title"'), ('aria-labelledby="compass-title"', 'aria-labelledby="amb-compass-title"')]:
        if old not in svg:
            raise SystemExit(f"quicklook: diagram no longer contains {old!r}")
        svg = svg.replace(old, new)
    return svg


def quicklook_runs():
    runs = []
    for slug, label, ask in RUNS:
        md = (ROOT / "examples" / f"{slug}.md").read_text()
        runs.append(
            f'<details class="amb-run"><summary><span>{label}</span><code>{html.escape(ask)}</code></summary>'
            f'<div class="amb-out">{render(md)}</div></details>'
        )
    return "\n".join(runs)


def build_quicklook(target):
    fragment = (ROOT / "site" / "quicklook.html").read_text()
    fragment = fragment.replace("{{diagram}}", quicklook_diagram()).replace("{{runs}}", quicklook_runs())
    # It lands inside a JS template literal.
    literal = "`\n" + fragment.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + "        `"
    page = target.read_text()
    a, b = page.index(QUICKLOOK_START) + len(QUICKLOOK_START), page.index(QUICKLOOK_END)
    target.write_text(page[:a] + literal + page[b:])
    print("quicklook written to", target)


if __name__ == "__main__":
    check_frontmatter()
    build_page()
    build_zip()
    if "--quicklook" in sys.argv:
        build_quicklook(pathlib.Path(sys.argv[sys.argv.index("--quicklook") + 1]).expanduser())
    print("built", SITE)
