"""Shared data-path resolution for the MIDOG2022 frozen-subset pipeline.

The frozen data may live either in ``data/`` next to the task card or in the
physical data location referenced by ``data/DATA_LOCATION.md``.  This module
searches a small list of candidate roots and exposes the resolved paths.
"""
from __future__ import annotations
import os

TASK_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # task card dir
SOLUTION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))               # agent_solution/
REPO_ROOT = TASK_DIR

DATA_ROOTS = [
    os.path.join(REPO_ROOT, "data"),
    os.path.join(REPO_ROOT, "data"),
    os.path.join(os.path.dirname(REPO_ROOT), "data"),
    "/mnt/f/dataset/biomed/2508.04441_mitotic_benchmark",
    os.path.join(os.path.expanduser("~"), "dataset", "biomed", "2508.04441_mitotic_benchmark"),
]

DEFAULT_PNG_NAMES = ["002.png", "008.png", "024.png", "063.png"]
DEFAULT_JSON_NAME = "MIDOG2022_training_png.json"


def resolve_data_root(explicit_root: str | None = None) -> str:
    if explicit_root is not None:
        return explicit_root
    for root in DATA_ROOTS:
        if os.path.isfile(os.path.join(root, DEFAULT_JSON_NAME)):
            return root
    raise FileNotFoundError(
        "Could not locate frozen MIDOG2022 data. Pass --data-root explicitly. "
        f"Looked in: {DATA_ROOTS}"
    )


def resolve_paths(explicit_root: str | None = None) -> tuple[str, ...]:
    """Return (json_path, png_path_002, ...) for the 4 frozen images.

    The frozen package may be split across locations (e.g. JSON next to the
    task card in data/, PNGs in the physical data root); each file is looked up
    independently over all candidate roots."""
    if explicit_root is not None:
        roots = [explicit_root]
    else:
        roots = DATA_ROOTS
    found = {}
    for name in [DEFAULT_JSON_NAME] + list(DEFAULT_PNG_NAMES):
        hits = [r for r in roots if os.path.isfile(os.path.join(r, name))]
        if not hits:
            raise FileNotFoundError(f"Frozen file not found anywhere: {name}")
        found[name] = os.path.join(hits[0], name)
    return (found[DEFAULT_JSON_NAME],) + tuple(found[n] for n in DEFAULT_PNG_NAMES)