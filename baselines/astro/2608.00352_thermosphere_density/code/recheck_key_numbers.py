#!/usr/bin/env python3
"""Minimal spot-check re-run for the judge (B dimension).

Recomputes the two key spot-check numbers directly from the frozen CSV only:
    W3 (2024-05-10..05-13): hourly min Dst = -406 @ 2024-05-11 02:00 UTC (n=96)
    W2 (2015-02-01..02-28): hourly min Dst = -69 (n=672)
Optionally W1 (2024-05-24..05-31): -28 @ 2024-05-31 19:00 UTC (n=192)

Requires only pandas (or stdlib csv). No paper numbers hardcoded.
Usage: python recheck_key_numbers.py [path/to/dst_hourly.csv]
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[datetime.datetime, int]]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        header = next(r)
        assert header == ["datetime_utc", "dst_nt"], header
        for line in r:
            t = dt.datetime.strptime(line[0], "%Y-%m-%d %H:%M:%S")
            rows.append((t, int(round(float(line[1])))))
    return rows


def window_min(rows, start: datetime.datetime, end: datetime.datetime):
    sub = [(t, v) for t, v in rows if start <= t <= end]
    m = min(sub, key=lambda x: x[1])
    return len(sub), m[1], m[0]


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        cand = Path(__file__).resolve().parents[2] / "data" / "dst_hourly.csv"
        if cand.exists():
            path = cand
        else:
            path = Path.cwd() / "data" / "dst_hourly.csv"
    rows = load(path)

    print("loaded", len(rows), "rows from", path.name)
    outcomes = []
    for name, (a, b, exp_n, exp_min, exp_t) in {
        "W1_quiet": (dt.datetime(2024, 5, 24), dt.datetime(2024, 5, 31, 23),
                     192, -28, "2024-05-31 19:00:00"),
        "W2_moderate": (dt.datetime(2015, 2, 1), dt.datetime(2015, 2, 28, 23),
                        672, -69, "2015-02-18 00:00:00"),
        "W3_extreme": (dt.datetime(2024, 5, 10), dt.datetime(2024, 5, 13, 23),
                       96, -406, "2024-05-11 02:00:00"),
    }.items():
        n, v, t = window_min(rows, a, b)
        ok = (n, v, t.strftime("%Y-%m-%d %H:%M:%S")) == (exp_n, exp_min, exp_t)
        outcomes.append((name, n, v, str(t), ok))
        print(f"{name}: n_hours={n} min_dst={v} @ {t}  expected=({exp_n},{exp_min},{exp_t}) -> {'OK' if ok else 'MISMATCH'}")

    print("\nALL SPOT-CHECKS PASS" if all(o[4] for o in outcomes)
          else "\nSOME CHECK(S) FAILED")
    return 0 if all(o[4] for o in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())