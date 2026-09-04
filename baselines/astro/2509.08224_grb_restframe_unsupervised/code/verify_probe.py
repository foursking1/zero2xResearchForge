#!/usr/bin/env python3
"""verify_probe.py - independent recomputation of the 3 rubric probe numbers.

Recomputes from raw 152-byte fixed-width lines (latin-1), independent of
reproduce.py's parser, to guard the evidence:
  1. total rows                     -> 320
  2. Type I count (I + I+EE)        -> 45
  3. Type I median T90z             -> 0.27 s

Usage:
    python3 verify_probe.py [path/to/tablea1.dat]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [
    "/mnt/f/dataset/astro/2509.08224_grb_restframe_unsupervised/tablea1.dat",
    os.path.join(HERE, "..", "data", "tablea1.dat"),
    os.environ.get("GRB_DATA_DIR", "") + "/tablea1.dat",
]


def parse(path):
    with open(path, "rb") as f:
        data = f.read()
    rows = data.rstrip(b"\n").split(b"\n")
    out = []
    for ln in rows:
        pad = (ln + b" " * 152)[:152]
        grb = pad[0:7].decode("latin-1").strip()
        t90 = pad[10:17].decode("latin-1").strip()
        typ = pad[98:105].decode("latin-1").strip()
        out.append((grb,
                    0.0 if t90 == "" else float(t90.replace("D", "E")),
                    typ))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else next(
        c for c in CANDIDATES if c and os.path.isfile(c))
    parsed = parse(path)
    total = len(parsed)
    typeI = [t for _, _, t in parsed if t in ("I", "I+EE")]
    t90I = sorted(t90 for _, t90, t in parsed if t in ("I", "I+EE"))
    n = len(t90I)
    median = (t90I[n // 2] + t90I[n // 2 - 1]) / 2.0 if n % 2 == 0 else t90I[n // 2]
    print(f"total rows            : {total}")
    print(f"Type I (I + I+EE)     : {len(typeI)}")
    print(f"Type I median T90z    : {median:.2f} s")
    checks = {
        "total_rows == 320": total == 320,
        "Type I count == 45": len(typeI) == 45,
        "Type I median T90z == 0.27": abs(median - 0.27) < 1e-9,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print(f"[{'PASS' if v else 'FAIL'}] {k}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()