"""Resolve task specifications and maintainer-only evaluation material.

Participant-facing task directories contain only ``TASK.md``. The paper
anchors, score rubrics, and calibration notes live under a separate maintainer
root and are never part of the Participant Kit.
"""
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.environ.get("PAPER_BENCH_ROOT", Path(__file__).resolve().parents[1])).resolve()
TASKS = ROOT / "tasks"
PRIVATE_FILES = frozenset({"PAPER_ANCHOR.md", "SCORE_RUBRIC.md", "CALIBRATION.md"})


def private_card_root() -> Path:
    configured = os.environ.get("PAPER_BENCH_PRIVATE_CARD_ROOT")
    return Path(configured).expanduser().resolve() if configured else ROOT / "evaluation" / "private" / "cards"


def private_card_dir(card_dir: str | Path) -> Path:
    card = Path(card_dir).resolve()
    try:
        relative = card.relative_to(TASKS)
    except ValueError as error:
        raise ValueError(f"task directory is outside {TASKS}: {card}") from error
    return private_card_root() / relative


def material_path(card_dir: str | Path, name: str) -> Path:
    if name in PRIVATE_FILES:
        return private_card_dir(card_dir) / name
    return Path(card_dir) / name


def required_paths(card_dir: str | Path) -> dict[str, Path]:
    return {
        "TASK.md": material_path(card_dir, "TASK.md"),
        **{name: material_path(card_dir, name) for name in sorted(PRIVATE_FILES)},
    }
