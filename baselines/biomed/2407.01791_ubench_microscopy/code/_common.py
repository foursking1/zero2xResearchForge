"""Shared helpers for the mu-Bench reproduction script suite.

Task: 2407.01791_ubench_microscopy
Data: frozen Arrow shard `ubench-test-00000-of-00007.arrow` (perception test split,
      shard 1 of 7). All scripts read that single frozen shard.
"""
import io
import os

import numpy as np
import pandas as pd
import pyarrow as pa
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # agent_solution/
DATA = os.environ.get(
    "UBENCH_ARROW",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                 "data", "ubench-test-00000-of-00007.arrow"))                # <task>/data/... (env-overridable)
RESULTS = os.path.join(ROOT, "results")
CODE = os.path.join(ROOT, "code")
EVIDENCE = os.path.join(ROOT, "evidence")
FEATURES = os.path.join(ROOT, "features")
os.makedirs(RESULTS, exist_ok=True)
os.makedirs(EVIDENCE, exist_ok=True)
os.makedirs(FEATURES, exist_ok=True)

QUESTION_NAMES = ["classification", "domain", "modality", "stain",
                  "subdomain", "submodality"]
# Coarse-grained perception levels (paper L1..L5); fine-grained = classification (L6)
COARSE_TYPES = ["modality", "submodality", "domain", "subdomain", "stain"]
FINE_TYPES = ["classification"]


def load_arrow_questions():
    """Read the frozen Arrow stream and return a long-form DataFrame.

    One row per (image, closed-VQA question). Includes the per-question option
    list, the correct answer as index and as string, plus image-level metadata.
    """
    mm = pa.memory_map(DATA)
    reader = pa.ipc.open_stream(mm)
    records = []
    for batch in reader:
        tbl = batch.to_pandas()
        for i, row in tbl.iterrows():
            img = row["image"]
            img_bytes = img["bytes"] if isinstance(img, dict) else img
            qs = row["questions"]
            if qs is None:
                continue
            for qname in QUESTION_NAMES:
                q = qs.get(qname) if isinstance(qs, dict) else None
                if q is None or not q.get("question"):
                    continue
                rec = {
                    "image_id": row["image_id"],
                    "image_bytes": img_bytes,
                    "dataset": row["dataset"],
                    "domain_meta": row["domain"],
                    "modality_meta": row["modality"],
                    "subdomain_meta": row["subdomain"],
                    "submodality_meta": row["submodality"],
                    "stain_meta": row["stain"],
                    "label_name": row["label_name"],
                    "question_type": qname,
                    "question_id": q.get("id"),
                    "question": q.get("question"),
                    "options": list(q.get("options")) if q.get("options") is not None else [],
                    "answer_idx": int(q["answer_idx"]),
                    "answer": q.get("answer"),
                }
                records.append(rec)
    return pd.DataFrame(records)


def decode_image_bytes(b):
    """Decode PNG/JPEG bytes to an RGB PIL image (mode coerced to RGB)."""
    return Image.open(io.BytesIO(b)).convert("RGB")