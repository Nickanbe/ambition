"""python -m contacts IN.json [OUT.json]  -- merge a JSON list of contact records."""

import json
import sys

from .dedupe import merge_contacts


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as f:
        records = json.load(f)
    merged = merge_contacts(records)
    text = json.dumps(merged, indent=2, ensure_ascii=False)
    if len(argv) > 1:
        with open(argv[1], "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
    print(f"{len(records)} records -> {len(merged)} contacts", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
