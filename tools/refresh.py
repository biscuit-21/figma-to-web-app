#!/usr/bin/env python3
"""Replace the bundled snapshot with live observations from the FRED API.

    export FRED_API_KEY=your_key_here
    python3 tools/refresh.py [--force] && python3 tools/build.py

Skips the pull if the data was already refreshed today, unless --force is
given. FRED series update on agency release schedules, so more than one pull a
day is wasted effort.

A key is free from https://fredaccount.stlouisfed.org/apikeys.

Each series in data.json carries a "pull" block describing how to request it:
FRED's own transform ("units") plus the frequency and, where the source series
is daily or weekly, the aggregation used to reduce it to months. Nothing is
computed here that FRED cannot compute itself, so the refreshed numbers are the
published ones rather than a reconstruction.

Only the numbers change. The titles, descriptions and commentary in data.json
are ours and are left alone.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data.json"
API = "https://api.stlouisfed.org/fred/series/observations"
TIMEOUT = 12      # FRED answers in well under a second when healthy
RETRIES = 2


def month_index(date: str, start_y: int, start_m: int) -> int:
    y, m = int(date[0:4]), int(date[5:7])
    return (y - start_y) * 12 + (m - start_m)


def fetch(series_id: str, pull: dict, key: str, start: str) -> list[tuple[str, float]]:
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "observation_start": f"{start}-01",
        "units": pull.get("units", "lin"),
        "frequency": pull.get("freq", "m"),
    }
    if "agg" in pull:
        params["aggregation_method"] = pull["agg"]

    url = f"{API}?{urllib.parse.urlencode(params)}"
    last_err: Exception | None = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "key-indicators/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                payload = json.load(r)
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            if e.code in (400, 403):
                raise SystemExit(f"FRED rejected the request for {series_id}: {e.code} {body}")
            last_err = e
        except Exception as e:  # network hiccup, rate limit
            last_err = e
        time.sleep(1.0 * (attempt + 1))
    else:
        raise SystemExit(f"could not fetch {series_id}: {last_err}")

    out = []
    for o in payload.get("observations", []):
        if o["value"] in (".", "", None):
            continue          # FRED marks missing observations with a dot
        out.append((o["date"], float(o["value"])))
    return out


def align(obs: list[tuple[str, float]], start_y: int, start_m: int, step: int,
          decimals: int) -> list[float]:
    """Place observations on the contiguous grid the dashboard expects."""
    grid: dict[int, float] = {}
    for date, v in obs:
        i = month_index(date, start_y, start_m)
        if i < 0 or i % step:
            continue
        grid[i // step] = v
    if not grid:
        return []
    last = max(grid)
    values, prev = [], None
    for j in range(last + 1):
        v = grid.get(j, prev)          # carry the previous value across any gap
        if v is None:
            continue
        values.append(round(v, decimals))
        prev = v
    return values


def main() -> int:
    force = "--force" in sys.argv

    data_preview = json.loads(DATA.read_text(encoding="utf-8"))
    today = time.strftime("%Y-%m-%d")
    if data_preview.get("asOf") == today and not force:
        print(f"Data was already refreshed today ({today}). Use --force to pull again.")
        return 0

    key = os.environ.get("FRED_API_KEY", "").strip()
    if not key:
        print("Set FRED_API_KEY first. Get a free key at "
              "https://fredaccount.stlouisfed.org/apikeys", file=sys.stderr)
        return 1

    data = data_preview
    start_y, start_m = int(data["start"][:4]), int(data["start"][5:7])

    failures = []
    for s in data["series"]:
        pull = s.get("pull")
        if not pull:
            print(f"  {s['id']:<16} skipped — no pull config")
            continue
        step = 3 if s["freq"] == "q" else 1
        try:
            obs = fetch(s["fred"], pull, key, data["start"])
            values = align(obs, start_y, start_m, step, s["decimals"])
        except SystemExit as e:
            print(f"  {s['id']:<16} FAILED — {e}")
            failures.append(s["id"])
            continue

        if len(values) < 8:
            print(f"  {s['id']:<16} FAILED — only {len(values)} usable observations")
            failures.append(s["id"])
            continue

        s["values"] = values
        if obs:
            s["release"] = f"latest observation {obs[-1][0]}"
        print(f"  {s['id']:<16} {len(values):>4} points, last {values[-1]}")
        time.sleep(0.15)          # stay well inside FRED's rate limit

    if failures:
        print(f"\n{len(failures)} series failed: {', '.join(failures)}", file=sys.stderr)
        print("data.json was NOT written.", file=sys.stderr)
        return 1

    data["asOf"] = time.strftime("%Y-%m-%d")
    DATA.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"\nwrote {DATA.relative_to(ROOT)} — now run: python3 tools/build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
