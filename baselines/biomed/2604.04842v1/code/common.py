"""Shared configuration and utilities for the PCSA reproduction analysis.

All data is read IN PLACE from the frozen data root (F:/dataset/2604.04842v1);
no files are copied and nothing is downloaded.

Author: research execution agent
Date: 2026-08-13
"""
import json
import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (frozen data, read-only)
# ---------------------------------------------------------------------------
DATA_ROOT = Path(os.environ.get(
    "PCSA_DATA_ROOT",
    "F:/dataset/2604.04842v1",
))

CACTUS_RAW = DATA_ROOT / "data" / "cactus_raw" / "all_dialogues.jsonl"
CACTUS_NEG = DATA_ROOT / "data" / "cactus_filtered" / "negative_dialogues.jsonl"
CARES_TRAIN = DATA_ROOT / "data" / "care_benchmark" / "train.jsonl"
CARES_TEST = DATA_ROOT / "data" / "care_benchmark" / "test.jsonl"
PERSONA_PROFILES = DATA_ROOT / "data" / "persona_profiles.jsonl"
RAW_OUTPUTS = DATA_ROOT / "results" / "raw_outputs"
PAPER_PDF = DATA_ROOT / "arxiv_2604.04842v1.pdf"

# Baselines module from the frozen reproduction workspace
BASELINES_PY = DATA_ROOT / "code" / "baselines" / "__init__.py"


def load_jsonl(path, limit=None):
    """Load a JSONL file into a list of dicts (in place, read-only)."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------
def clean_text(text):
    """Normalise whitespace for perplexity / n-gram analysis."""
    text = re.sub(r"\s+", " ", str(text))
    return text.strip()


def tokenize(text, lowercase=True):
    """Simple whitespace tokenisation with optional lowercasing."""
    text = clean_text(text)
    if lowercase:
        text = text.lower()
    if not text:
        return []
    return text.split(" ")
