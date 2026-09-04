"""Shared path helpers for the QED-Nano reproduction analysis.

INPUT  paths (frozen data, read-only):
  - repro_root()    reproduction workspace root (results JSONL, PDF)   default F:/dataset/2604.04898v1
  - hf_root()       HuggingFace dataset snapshot (parquet)            default E:/scisolvebench-data/raw/2604.04898v1/huggingface
  - repro_results() frozen reproduction output directory              <repro_root>/results

OUTPUT paths (deliverables, written under the task working directory):
  - output_dir()    <agent_solution>/results   (agent_solution is the parent of code/)
  - figure_dir()    <agent_solution>/results/figures

The `data/huggingface` entry under the reproduction root is an MSYS symlink that native
Windows Python does not follow, so we resolve the real directory by probing candidate
locations.  All paths can be overridden with environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------------
# Frozen-data roots (input) -- first candidate that exists wins
# ----------------------------------------------------------------------------
_REPRO_CANDIDATES = [
    os.environ.get("QEDNANO_REPRO_ROOT", "F:/dataset/2604.04898v1"),
    os.environ.get("QEDNANO_REPRO_ROOT", "D:/project/paper-bench/tasks_legacy/2604.04898v1"),
]

_HF_CANDIDATES = [
    os.environ.get("QEDNANO_HF_ROOT", "E:/scisolvebench-data/raw/2604.04898v1/huggingface"),
    os.environ.get("QEDNANO_HF_ROOT", "F:/scisolvebench-data/raw/2604.04898v1/huggingface"),
    "F:/dataset/2604.04898v1/data/huggingface",
    "D:/project/paper-bench/tasks_legacy/2604.04898v1/data/huggingface",
]


def repro_root() -> Path:
    for cand in _REPRO_CANDIDATES:
        p = Path(cand)
        if p.is_dir():
            return p
    raise FileNotFoundError("Could not locate reproduction workspace root (tried %r)" % _REPRO_CANDIDATES)


def hf_root() -> Path:
    for cand in _HF_CANDIDATES:
        p = Path(cand)
        if p.is_dir():
            return p
    link = repro_root() / "data" / "huggingface"
    if link.is_dir():
        return link
    raise FileNotFoundError(
        "Could not locate HuggingFace dataset snapshot. Tried %r" % _HF_CANDIDATES
    )


def repro_results() -> Path:
    """Frozen reproduction output directory (input JSONL / summary files)."""
    return repro_root() / "results"


def output_dir() -> Path:
    """Deliverables directory: <task_workdir>/agent_solution/results."""
    # common.py lives at <task_workdir>/agent_solution/code/common.py,
    # so parents[1] is the agent_solution directory.
    base = Path(__file__).resolve().parents[1]
    out = base / "results"
    out.mkdir(parents=True, exist_ok=True)
    return out


def figure_dir() -> Path:
    d = output_dir() / "figures"
    d.mkdir(parents=True, exist_ok=True)
    return d


def dataset_path(dataset: str, fname: str) -> Path:
    """Return the parquet path for `dataset` (e.g. IMOProofBench) and `fname`."""
    return hf_root() / dataset / "data" / fname


def paper_pdf() -> Path:
    root = repro_root()
    for name in ("2604.04898v1.pdf", "arxiv_2604.04898v1.pdf"):
        p = root / name
        if p.is_file():
            return p
    raise FileNotFoundError("paper PDF not found under %s" % root)
