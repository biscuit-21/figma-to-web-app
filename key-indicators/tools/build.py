#!/usr/bin/env python3
"""Inject tools/data.json into tools/template.html and write web/index.html.

    python3 tools/build.py

The dashboard ships as one self-contained HTML file with no runtime fetches,
so the dataset is compiled in rather than loaded. Run this after changing
either the template or the data.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "tools" / "template.html"
DATA = ROOT / "tools" / "data.json"
OUT = ROOT / "web" / "index.html"

PLACEHOLDER = "/*__DATA__*/"


def main() -> int:
    if not TEMPLATE.exists():
        print(f"missing template: {TEMPLATE}", file=sys.stderr)
        return 1
    if not DATA.exists():
        print(f"missing data: {DATA}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        print(f"template has no {PLACEHOLDER} placeholder", file=sys.stderr)
        return 1

    raw = DATA.read_text(encoding="utf-8")
    data = json.loads(raw)  # fail loudly on malformed JSON

    required = {"start", "asOf", "categories", "series"}
    missing = required - set(data)
    if missing:
        print(f"data.json is missing keys: {', '.join(sorted(missing))}", file=sys.stderr)
        return 1

    for s in data["series"]:
        if not s.get("values"):
            print(f"series {s.get('id')} has no values", file=sys.stderr)
            return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(template.replace(PLACEHOLDER, json.dumps(data, separators=(",", ":"))),
                   encoding="utf-8")

    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)} — {len(data['series'])} series, "
          f"current to {data['asOf']}, {kb:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
