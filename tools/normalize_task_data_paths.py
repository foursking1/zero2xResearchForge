#!/usr/bin/env python3
"""Replace legacy local data paths in task cards with PaperBench variables."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
DOMAINS = {"astro", "biomed", "cs", "earth", "materials"}
DATA_ENV = "$PAPER_BENCH_DATA_DIR"
DATA_ROOT_ENV = "$PAPER_BENCH_DATA_ROOT"
LEGACY_PATH = re.compile(
    r"(?<![A-Za-z0-9_])(?:[EF]:[\\/]|/mnt/[ef]/)[^\s`'\"<>()\uFF08\uFF09\uFF0C\u3002\uFF1B\uFF1A]*",
    flags=re.IGNORECASE,
)


def replacement(raw: str, card_id: str) -> str:
    normalized = raw.replace("\\", "/")
    if normalized.lower().startswith("/mnt/"):
        parts = normalized.split("/")[3:]
    else:
        parts = normalized.split("/")[1:]
    parts = [part for part in parts if part]
    if parts and parts[0].lower() == "dataset":
        parts = parts[1:]
    if not parts:
        return DATA_ROOT_ENV
    if parts[0].startswith("DATA_MOVE_LOG_"):
        return f"{DATA_ROOT_ENV}/checksums.sha256"
    if parts[0] in DOMAINS and len(parts) >= 2 and parts[1] == card_id:
        parts = parts[2:]
    elif parts[0] == "legacy" and len(parts) >= 2 and parts[1] == card_id:
        parts = parts[2:]
    elif parts[0] == card_id:
        parts = parts[1:]
    return DATA_ENV if not parts else f"{DATA_ENV}/{'/'.join(parts)}"


def normalize_task(task_file: Path, write: bool) -> tuple[bool, int]:
    card_id = task_file.parent.name
    with task_file.open("r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    replaced, count = LEGACY_PATH.subn(lambda match: replacement(match.group(0), card_id), text)
    banner = (
        f"> Internal data root: `{DATA_ENV}`. Run this card through `paperbench.py run`; "
        f"verify the downloaded mirror with `{DATA_ROOT_ENV}/checksums.sha256`."
    )
    # Keep the portable-data contract directly below the title even for cards
    # that contain a mixture of LF and CRLF lines. Rebuild only the title area
    # so repeated maintenance runs cannot accumulate blank lines.
    lines = replaced.splitlines(keepends=True)
    if not lines:
        lines = [""]
    title = lines[0]
    title_newline = "\r\n" if title.endswith("\r\n") else "\n"
    body = [line for line in lines[1:] if line.rstrip("\r\n") != banner]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    replaced = f"{title}{title_newline}{banner}{title_newline}{title_newline}{''.join(body)}"
    changed = replaced != text
    if changed and write:
        with task_file.open("w", encoding="utf-8", newline="") as handle:
            handle.write(replaced)
    return changed, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite task cards in place")
    args = parser.parse_args()
    changed = 0
    replaced = 0
    remaining = []
    for task_file in sorted(TASKS.glob("*/*/TASK.md")):
        file_changed, count = normalize_task(task_file, args.write)
        changed += int(file_changed)
        replaced += count
        with task_file.open(encoding="utf-8", errors="replace") as handle:
            if LEGACY_PATH.search(handle.read()):
                remaining.append(task_file)
    mode = "rewritten" if args.write else "would rewrite"
    print(f"{mode}: files={changed} legacy_paths={replaced}")
    if remaining:
        print("legacy paths remain:", file=sys.stderr)
        for task_file in remaining:
            print(f"  - {task_file.relative_to(ROOT)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
