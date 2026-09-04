#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py
==========
End-to-end reproducible pipeline for the PatternNet (1706.03424) retrieval
reproduction: extract features from the frozen parquet shards -> run the
every-image-as-query retrieval evaluation -> per-class evidence -> analysis.

    python run_all.py --out-root <agent_solution> --model resnet18 --device cpu

The default `--out-root` is the submission/ directory that already contains the
scripts; artifacts/ and results/ are created inside it.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}\n", flush=True)
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", default=str(HERE.parent),
                    help="root dir containing scripts/, artifacts/, results/")
    ap.add_argument("--model", default="resnet18", choices=["resnet18", "vit_b_16"])
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"])
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--sample-per-class", type=int, default=0,
                    help="0 = full every-image-as-query protocol")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-extract", action="store_true")
    ap.add_argument("--batch-size", type=int, default=64)
    aa = ap.parse_args()

    root = Path(aa.out_root)
    scripts = HERE
    art = root / "artifacts"
    res = root / "results"

    if not aa.skip_extract:
        run([
            sys.executable, str(scripts / "extract_features.py"),
            "--data-dir", aa.data_dir or "",
            "--out-dir", str(art),
            "--model", aa.model,
            "--device", aa.device,
            "--batch-size", str(aa.batch_size),
        ])

    feat = art / f"features_{aa.model}.npy"
    labs = art / "labels.npy"
    cnames = art / "class_names.json"

    run([
        sys.executable, str(scripts / "evaluate_retrieval.py"),
        "--features", str(feat),
        "--labels", str(labs),
        "--out-dir", str(res),
        "--class-names", str(cnames),
        "--sample-per-class", str(aa.sample_per_class),
        "--seed", str(aa.seed),
        "--dump-per-query",
    ])

    run([
        sys.executable, str(scripts / "analysis.py"),
        "--features", str(feat),
        "--labels", str(labs),
        "--evidence", str(res / "evidence_table.csv"),
        "--class-names", str(cnames),
        "--out-dir", str(res),
    ])

    print("\n[run_all] pipeline complete.")


if __name__ == "__main__":
    main()