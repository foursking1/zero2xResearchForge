#!/usr/bin/env python3
"""Prepare the complete frozen PaperBench input-data mirror for ModelScope.

The source of truth is F:/dataset/DATA_MOVE_LOG_*.tsv.  Those logs identify
frozen task input files and their source SHA-256 checksums.  The tool never
walks agent_solution/ or E:/scisolvebench-data, which may contain submissions,
private references, or scratch material.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
DEFAULT_FROZEN_ROOT = Path("/mnt/f/dataset")
SKIP_NAMES = {"DATA_LOCATION.md"}
SANITIZE_NAMES = {
    "SOURCE.md", "README.md", "LICENSE", "LICENSE_CCBY4.txt",
    "MANIFEST.tsv", "CHECKSUMS.sha256", "checksums.sha256",
    "CHECKSUMS_SHA256.tsv", "source_manifest.json",
}
LOCAL_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:[A-Za-z]:[\\/]|/(?:mnt|home|Users)/)[^\s`'\")]+"
)


@dataclass(frozen=True)
class ReleaseFile:
    target: PurePosixPath
    source: Path
    domain: str
    card: str
    source_kind: str
    source_reference: str
    source_sha256: str


def cards() -> set[tuple[str, str]]:
    with (ROOT / "cards.csv").open(encoding="utf-8-sig", newline="") as handle:
        return {(row["domain"], row["card_id"]) for row in csv.DictReader(handle)}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def normalized_relative(value: str, card: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe frozen-log path: {value!r}")
    parts = path.parts[1:] if path.parts[0] == card else path.parts
    if not parts:
        raise ValueError(f"empty frozen-log path after card prefix: {value!r}")
    return PurePosixPath(*parts)


def locate_frozen_file(frozen_root: Path, domain: str, card: str,
                       original_relative: str, relative: PurePosixPath) -> Path | None:
    original = PurePosixPath(original_relative.replace("\\", "/"))
    card_root = frozen_root / domain / card
    if original.parts and original.parts[0] == card:
        candidates = [
            frozen_root / domain / Path(*original.parts),
            card_root / Path(*relative.parts),
        ]
    else:
        candidates = [
            card_root / Path(*relative.parts),
            frozen_root / domain / Path(*relative.parts),
            frozen_root / card / Path(*relative.parts),
        ]
    # Some historical move-log entries omit the task-local ``data`` wrapper.
    # AID's multi-label parquet was also quarantined during the data migration.
    candidates.extend((
        card_root / "data" / Path(*relative.parts),
        card_root / "data" / "labels" / Path(*relative.parts),
        card_root / "data_multilabel_quarantine" / relative.name,
    ))
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def frozen_records(frozen_root: Path) -> tuple[list[ReleaseFile], list[str], int]:
    valid_cards = cards()
    records: dict[PurePosixPath, ReleaseFile] = {}
    missing: list[str] = []
    ignored = 0
    for log in sorted(frozen_root.glob("DATA_MOVE_LOG_*.tsv")):
        with log.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.reader(handle, delimiter="\t"):
                if len(row) < 4:
                    continue
                domain, card, original_relative, expected_hash = row[:4]
                domain = domain.lstrip("\ufeff")
                if (domain, card) not in valid_cards:
                    ignored += 1
                    continue
                try:
                    relative = normalized_relative(original_relative, card)
                except ValueError as error:
                    missing.append(f"{domain}/{card}\t{error}")
                    continue
                source = locate_frozen_file(frozen_root, domain, card, original_relative, relative)
                target = PurePosixPath(domain, card, *relative.parts)
                if source is None:
                    missing.append(f"{domain}/{card}\tmissing\t{original_relative}")
                    continue
                record = ReleaseFile(
                    target=target,
                    source=source,
                    domain=domain,
                    card=card,
                    source_kind="frozen_log",
                    source_reference=original_relative.replace("\\", "/"),
                    source_sha256=expected_hash.lower(),
                )
                existing = records.get(target)
                if existing and existing.source_sha256 != record.source_sha256:
                    # Historical move logs sometimes retained an obsolete hash
                    # alongside the current path. Keep the entry that matches
                    # the file currently preserved in the frozen root.
                    existing_matches = digest(existing.source) == existing.source_sha256
                    record_matches = digest(record.source) == record.source_sha256
                    if record_matches and not existing_matches:
                        records[target] = record
                    elif existing_matches and not record_matches:
                        continue
                    else:
                        missing.append(f"{domain}/{card}\tconflicting target\t{target}")
                else:
                    records[target] = record
    return sorted(records.values(), key=lambda record: record.target.as_posix()), missing, ignored


def task_data_records(existing: set[PurePosixPath]) -> list[ReleaseFile]:
    records: list[ReleaseFile] = []
    for domain, card in sorted(cards()):
        data_dir = TASKS / domain / card / "data"
        if not data_dir.is_dir() or data_dir.is_symlink():
            continue
        for source in sorted(path for path in data_dir.rglob("*") if path.is_file()):
            if source.name in SKIP_NAMES:
                continue
            target = PurePosixPath(domain, card, *source.relative_to(data_dir).parts)
            if target in existing:
                continue
            records.append(ReleaseFile(
                target=target,
                source=source,
                domain=domain,
                card=card,
                source_kind="task_data",
                source_reference=source.relative_to(data_dir).as_posix(),
                source_sha256="",
            ))
    return records


def write_inventory(output: Path, records: list[ReleaseFile], missing: list[str], ignored: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    fields = ("target_path", "card", "source_kind", "source_reference", "source_sha256", "bytes")
    with (output / "data_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({
                "target_path": record.target.as_posix(),
                "card": f"{record.domain}/{record.card}",
                "source_kind": record.source_kind,
                "source_reference": record.source_reference,
                "source_sha256": record.source_sha256,
                "bytes": record.source.stat().st_size,
            })
    (output / "missing_frozen_files.tsv").write_text(
        "\n".join(missing) + ("\n" if missing else ""), encoding="utf-8"
    )
    total = sum(record.source.stat().st_size for record in records)
    card_count = len({(record.domain, record.card) for record in records})
    (output / "README.md").write_text("\n".join([
        "# PaperBench complete frozen-data mirror staging",
        "",
        f"- Task inputs represented: {card_count}",
        f"- Files represented: {len(records)}",
        f"- Input bytes represented: {total}",
        f"- Non-card log entries ignored: {ignored}",
        f"- Frozen-log entries missing locally: {len(missing)}",
        "",
        "The upload payload is organized as `<domain>/<card_id>/...` and is intended",
        "to be used as `PAPER_BENCH_DATA_ROOT`. It contains frozen task inputs only.",
        "It excludes agent solutions, private judge material, E: asset candidates,",
        "and scratch files.",
        "",
    ]), encoding="utf-8")


def copy_metadata(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8", errors="replace")
    target.write_text(LOCAL_PATH_PATTERN.sub("<local-path>", text), encoding="utf-8")


def link_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source)


def stage_payload(output: Path, records: list[ReleaseFile]) -> None:
    payload = output / "payload"
    if payload.exists():
        raise RuntimeError(f"staging directory already exists: {payload}")
    payload.mkdir()
    checksums: list[str] = []
    inventory_rows: list[dict[str, str]] = []
    for record in records:
        target = payload / record.target
        if record.source.name in SANITIZE_NAMES:
            copy_metadata(record.source, target)
            payload_hash = digest(target)
        else:
            link_file(record.source, target)
            payload_hash = record.source_sha256 or digest(record.source)
        checksums.append(f"{payload_hash}  {record.target.as_posix()}")
        inventory_rows.append({
            "target_path": record.target.as_posix(),
            "card": f"{record.domain}/{record.card}",
            "source_kind": record.source_kind,
            "source_reference": record.source_reference,
            "source_sha256": record.source_sha256,
            "payload_sha256": payload_hash,
        })
    (payload / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    with (payload / "data_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory_rows[0]))
        writer.writeheader()
        writer.writerows(inventory_rows)
    (payload / ".gitattributes").write_text("\n".join([
        "# Preserve every frozen input byte through ModelScope Git LFS.",
        "* filter=lfs diff=lfs merge=lfs -text",
        "README.md -filter -diff -merge text",
        "checksums.sha256 -filter -diff -merge text",
        "data_inventory.csv -filter -diff -merge text",
        ".gitattributes -filter -diff -merge text",
        "",
    ]), encoding="utf-8")
    (payload / "README.md").write_text("\n".join([
        "---",
        "license: other",
        "tags:",
        "- benchmark",
        "- scientific-computing",
        "- paper-bench",
        "---",
        "",
        "# PaperBench frozen task data",
        "",
        "This mirror contains the frozen task inputs required by PaperBench.",
        "The layout is `<domain>/<card_id>/...`; download this repository and set",
        "`PAPER_BENCH_DATA_ROOT` to the downloaded root.",
        "",
        "`data_inventory.csv` records the source class and source checksum for each",
        "file. `checksums.sha256` validates the distributed files. All frozen inputs",
        "are stored through Git LFS to preserve their bytes. Local drive paths",
        "are not included. This mirror excludes agent solutions, private anchors,",
        "scoring rubrics, calibration material, reference results, and scratch data.",
        "",
        "Licenses and upstream attribution vary by source dataset; consult each",
        "task's public data manifest before redistribution or downstream use.",
        "",
    ]), encoding="utf-8")
    print(f"staged {len(records)} frozen input files at {payload}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-root", default=str(DEFAULT_FROZEN_ROOT))
    parser.add_argument("--output", default=str(ROOT / ".paperbench" / "modelscope-full"))
    parser.add_argument("--stage", action="store_true", help="create a symlinked upload payload")
    parser.add_argument("--allow-missing", action="store_true",
                        help="allow staging despite missing frozen-log files")
    args = parser.parse_args()
    frozen_root = Path(args.frozen_root).expanduser().resolve()
    if not frozen_root.is_dir():
        raise SystemExit(f"frozen root does not exist: {frozen_root}")
    records, missing, ignored = frozen_records(frozen_root)
    existing = {record.target for record in records}
    records.extend(task_data_records(existing))
    records.sort(key=lambda record: record.target.as_posix())
    output = Path(args.output).expanduser().resolve()
    write_inventory(output, records, missing, ignored)
    print(f"wrote inventory: {output}")
    print(f"records={len(records)} missing_frozen_files={len(missing)}")
    if args.stage:
        if missing and not args.allow_missing:
            raise SystemExit("refusing to stage with missing frozen-log files; pass --allow-missing to override")
        stage_payload(output, records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
