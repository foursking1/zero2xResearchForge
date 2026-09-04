#!/usr/bin/env python3
"""Assemble the deliverables into submission/ (per TASK.md) + evidence/.

Copies the final artifacts from agent_solution/ into the task root
`submission/` (report.md, solution.md, code/, results/ and small evidence
exports). The model checkpoint is large and lives only under agent_solution/.

Usage:
    python3 agent_solution/code/07_make_submission.py [--root .]
"""
import argparse
import shutil
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[2]   # .../tasks/earth/1709.00029_eurosat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(TASK_ROOT))
    args = ap.parse_args()
    root = Path(args.root)
    src = root / "agent_solution"
    dst = root / "submission"
    dst.mkdir(parents=True, exist_ok=True)

    items = ["report.md", "solution.md", "README.md"]
    for it in items:
        shutil.copy(src / it, dst / it)

    shutil.copytree(src / "code", dst / "code", dirs_exist_ok=True)
    shutil.copytree(src / "results", dst / "results", dirs_exist_ok=True)

    ev = dst / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    for it in ["results/metrics.json", "results/evidence_table.csv",
               "results/confusion_matrix.csv", "results/analysis.json"]:
        shutil.copy(src / it, ev / Path(it).name)

    print(f"submission assembled at {dst}")


if __name__ == "__main__":
    main()