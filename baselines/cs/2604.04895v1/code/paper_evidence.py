# -*- coding: utf-8 -*-
"""
paper_evidence.py
=================
Shared loaders for the frozen reproduction data of arXiv 2604.04895v1
("Agentic Federated Learning") and explicitly-cited values transcribed
from the paper PDF.

All paths point at the ORIGINAL frozen data location F:/dataset/2604.04895v1
(read-only).  Nothing is copied.

Two categories of data are handled here:

1. MACHINE-READABLE FROZEN DATA (independently analyzable)
   - data/official_artifacts/k_agent.csv   (CIFAR-10 K-Agent table = paper Table 1 CIFAR-10 half)
   - results/local_baseline_comparison.csv (MNIST smoke baselines, 5 clients / 3 rounds)
   - results/local_runs/*/raw/*.json       (per-round MNIST smoke logs)

2. PAPER-CITED VALUES (transcribed from the frozen PDF, NOT independently
   reproducible from raw data files).  Every value is tagged PAPER_CITED=True
   so downstream tables can clearly label provenance.
   - Table 1 MNIST half (K-Agent accuracies ~95-97%)
   - Table 2 (token / cost / accuracy for raw-LLM vs Tool-Agent, client counts 5..50)
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (original, read-only)
# ---------------------------------------------------------------------------
DATA_ROOT = Path("F:/dataset/2604.04895v1")
K_AGENT_CSV = DATA_ROOT / "data" / "official_artifacts" / "k_agent.csv"
BASELINE_CSV = DATA_ROOT / "results" / "local_baseline_comparison.csv"
LOCAL_RUNS = DATA_ROOT / "results" / "local_runs"

METHODS = ("oort", "poc", "random", "round_robin")
MODELS = ("qwen3:8b", "llama3.1:8b", "llama3.2:3b")
PROMPTS = ("chain-of-thought", "description-only", "few-shot")


def parse_sel(sel: str) -> tuple[str, str, str]:
    """Parse a 'prompt-method-model' selector, e.g. 'chain-of-thought-oort-qwen3:8b'."""
    for method in METHODS:
        for model in MODELS:
            m = re.search(rf"-(?:{method})-(?:{re.escape(model)})$", sel)
            if m:
                return sel[: m.start()], method, model
    return "unknown", "unknown", "unknown"


def load_k_agent_csv() -> list[dict]:
    rows = []
    with open(K_AGENT_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r["accuracy"] = float(r["accuracy"])
            r["std_accuracy"] = float(r["std_accuracy"])
            r["k_medio"] = float(r["k_medio"])
            r["k_std"] = float(r["k_std"])
            r["download_mb"] = float(r["download_mb"])
            r["sample_time"] = float(r["sample_time"])
            prompt, method, model = parse_sel(r["sel"])
            r["prompt"] = prompt
            r["method"] = method
            r["model"] = model
            rows.append(r)
    return rows


def load_baseline_comparison() -> list[dict]:
    rows = []
    with open(BASELINE_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for k in ("rounds", "best_round"):
                r[k] = int(r[k])
            for k in ("best_eval_accuracy", "final_eval_accuracy", "final_eval_loss",
                      "avg_selected_k", "avg_sample_time"):
                r[k] = float(r[k])
            rows.append(r)
    return rows


def load_smoke_run_json(run_name: str) -> dict:
    """Load the raw per-round JSON of a local smoke run."""
    raw_dir = LOCAL_RUNS / run_name / "raw"
    files = list(raw_dir.glob("timestamp_*.json"))
    if len(files) != 1:
        raise FileNotFoundError(f"Expected exactly one timestamp json in {raw_dir}, found {len(files)}")
    with open(files[0], encoding="utf-8") as fh:
        return json.load(fh)


def smoke_run_names() -> list[str]:
    return [d.name for d in LOCAL_RUNS.iterdir() if d.is_dir() and d.name.startswith("mnist-")]


# ---------------------------------------------------------------------------
# Paper-cited tables (transcribed from frozen PDF 2604.04895v1.pdf)
# ---------------------------------------------------------------------------

# Table 1 (MNIST half), columns: (prompt, model, method) -> (k_mean, k_std,
# accuracy_mean, accuracy_std, st_mean).  The frozen PDF's MNIST half is
# typeset in a compressed layout; values below are read from the PDF text.
# Accuracy is reported by the paper as % (e.g. 95,97 +- 3).
TABLE1_MNIST = [
    # (prompt, model, method, k_mean, k_std, acc_mean_pct, acc_std_pct, st_s)
    ("description-only", "qwen3:8b",   "poc",    7, 6, 95.97, 3, 4.00),
    ("description-only", "qwen3:8b",   "random", 6, 5, 96.90, 1, 8.65),
    ("description-only", "qwen3:8b",   "oort",   11, 6, 97.06, 1, 2.21),
    ("few-shot",         "qwen3:8b",   "poc",    7, 5, 96.68, 2, 1.67),
    ("few-shot",         "qwen3:8b",   "random", 5, 4, 96.32, 2, 1.74),
    ("few-shot",         "qwen3:8b",   "oort",   8, 6, 97.22, 1, 0.19),
    ("chain-of-thought", "qwen3:8b",   "poc",    7, 5, 96.50, 2, 1.63),
    ("chain-of-thought", "qwen3:8b",   "random", 8, 2, 95.25, 2, 0.18),
    ("chain-of-thought", "qwen3:8b",   "oort",   9, 6, 97.05, 1, 0.28),
    ("description-only", "llama3.1:8b", "poc",   10, 0, 96.04, 3, 0.17),
    ("description-only", "llama3.1:8b", "random", 10, 2, 96.66, 2, 0.18),
    ("description-only", "llama3.1:8b", "oort",   9, 2, 97.05, 1, 0.29),
    ("few-shot",         "llama3.1:8b", "poc",   10, 1, 95.76, 2, 0.16),
    ("few-shot",         "llama3.1:8b", "random", 6, 1, 95.86, 3, 0.34),
    ("few-shot",         "llama3.1:8b", "oort",   9, 1, 97.21, 1, 0.16),
    ("chain-of-thought", "llama3.1:8b", "poc",    8, 2, 96.64, 2, 0.26),
    ("chain-of-thought", "llama3.1:8b", "random", 8, 2, 95.89, 2, 0.21),
    ("chain-of-thought", "llama3.1:8b", "oort",   5, 1, 97.09, 1, 2.21),
    ("description-only", "llama3.2:3b", "poc",   10, 0, 95.00, 3, 0.31),
    ("description-only", "llama3.2:3b", "random", 9, 1, 96.64, 1, 0.20),
    ("description-only", "llama3.2:3b", "oort",   9, 1, 97.22, 1, 0.31),
    ("few-shot",         "llama3.2:3b", "poc",    9, 2, 96.26, 2, 0.16),
    ("few-shot",         "llama3.2:3b", "random", 7, 2, 96.13, 2, 0.14),
    ("few-shot",         "llama3.2:3b", "oort",   8, 1, 97.00, 1, 0.16),
    ("chain-of-thought", "llama3.2:3b", "poc",    9, 1, 96.13, 2, 0.19),
    ("chain-of-thought", "llama3.2:3b", "random", 8, 2, 96.25, 2, 0.18),
    ("chain-of-thought", "llama3.2:3b", "oort",   5, 1, 96.77, 1, 0.16),
]

# Table 2 : token / cost / accuracy scaling for raw-LLM vs Tool-Agent.
# Column layout in PDF (mean +- std):
#   N Clients | Approach | Completion Tokens | Prompt Tokens | Total Cost ($) | Total Tokens | Accuracy
TABLE2_RAW = [
    # (n_clients, approach, completion_mean, completion_std, prompt_mean, prompt_std,
    #  cost_mean, cost_std, total_tokens_mean, total_tokens_std, acc_mean, acc_std)
    (5,  "llm",   178, 52,  1336, 15,  0.000308, 0.000031, 1515, 54,  0.766264, 0.105471),
    (5,  "tool",  164, 122, 6193, 1963, 0.000804, 0.000241, 6358, 2072, 0.792612, 0.101721),
    (10, "llm",   218, 56,  2259, 28,  0.000470, 0.000035, 2478, 64,  0.693686, 0.066431),
    (10, "tool",  289, 218, 8367, 3103, 0.001149, 0.000431, 8657, 3297, 0.785554, 0.085655),
    (25, "llm",   254, 67,  5035, 73,  0.000908, 0.000041, 5289, 97,  0.637390, 0.090126),
    (25, "tool",  248, 244, 8056, 3275, 0.001080, 0.000484, 8305, 3493, 0.882115, 0.146230),
    (50, "llm",   241, 68,  9652, 145, 0.001593, 0.000044, 9894, 154, 0.728411, 0.126316),
    (50, "tool",  219, 223, 7185, 2343, 0.000961, 0.000325, 7404, 2539, 0.797055, 0.138048),
]


@dataclass
class PaperCited:
    """Marker for values transcribed from the frozen paper PDF."""
    source: str = "PAPER-CITED (frozen PDF 2604.04895v1.pdf)"
    PAPER_CITED: bool = True


PAPER_CITED_TABLE1_MNIST = PaperCited()
PAPER_CITED_TABLE2 = PaperCited()
