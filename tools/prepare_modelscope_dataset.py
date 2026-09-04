#!/usr/bin/env python3
"""Inventory and stage public task inputs for a ModelScope dataset repository.

This tool deliberately never considers agent_solution/, virtual environments, or
private evaluation files.  It writes a local catalog for all task input folders;
payload staging requires an explicit card allow-list.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
METADATA_NAMES = {
    "SOURCE.md", "DATA_LOCATION.md", "source_manifest.json", "MANIFEST.tsv",
    "CHECKSUMS.sha256", "checksums.sha256", "README.md", "LICENSE",
}
PUBLIC_LICENSE_MARKERS = ("cc by 4.0", "cc-by-4.0", "cc0", "cc-zero")
STAGED_METADATA_NAMES = {
    "SOURCE.md", "README.md", "LICENSE", "LICENSE_CCBY4.txt",
    "CHECKSUMS_SHA256.tsv", "CHECKSUMS.sha256", "checksums.sha256", "MANIFEST.tsv",
}
LOCAL_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z])(?:[A-Za-z]:[\\/]|/(?:mnt|home|Users)/)[^\s`'\")]+"
)


def cards() -> list[dict[str, str]]:
    with (ROOT / "cards.csv").open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def data_files(data_dir: Path) -> list[Path]:
    # Do not follow local-drive links into a public mirror.
    return sorted(
        path for path in data_dir.rglob("*") if path.is_file() and not path.is_symlink()
    )


def external_links(data_dir: Path) -> list[Path]:
    return sorted(path for path in data_dir.rglob("*") if path.is_symlink())


def source_evidence(card_dir: Path, data_dir: Path) -> tuple[str, str]:
    sources = [data_dir / "SOURCE.md", data_dir / "README.md", card_dir / "TASK.md"]
    texts = []
    for source in sources:
        if source.is_file():
            texts.append(source.read_text(encoding="utf-8", errors="replace")[:20000])
    combined = "\n".join(texts).lower()
    if any(marker in combined for marker in PUBLIC_LICENSE_MARKERS):
        status = "likely_republishable_review_required"
    elif "license" in combined or "许可" in combined:
        status = "license_present_manual_review_required"
    else:
        status = "no_license_evidence_upstream_download_only"
    evidence = next((str(path.relative_to(ROOT)) for path in sources if path.is_file()), "")
    return status, evidence


def build_catalog(output: Path) -> tuple[list[dict[str, str]], dict[str, list[Path]]]:
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    files_by_card: dict[str, list[Path]] = {}
    for card in cards():
        key = f"{card['domain']}/{card['card_id']}"
        card_dir = TASKS / card["domain"] / card["card_id"]
        data_dir = card_dir / "data"
        files = data_files(data_dir) if data_dir.is_dir() else []
        links = external_links(data_dir) if data_dir.is_dir() else []
        payload = [path for path in files if path.name not in METADATA_NAMES]
        total_bytes = sum(path.stat().st_size for path in files)
        payload_bytes = sum(path.stat().st_size for path in payload)
        status, evidence = source_evidence(card_dir, data_dir)
        rows.append({
            "card": key,
            "level": card.get("level", ""),
            "data_present": str(data_dir.is_dir()).lower(),
            "all_files": str(len(files)),
            "payload_files": str(len(payload)),
            "all_bytes": str(total_bytes),
            "payload_bytes": str(payload_bytes),
            "external_link_entries": str(len(links)),
            "availability": (
                "metadata_only" if not payload
                else "local_payload_plus_external_links" if links
                else "local_payload_only"
            ),
            "release_status": status,
            "license_evidence": evidence,
        })
        files_by_card[key] = files
    fields = list(rows[0]) if rows else []
    with (output / "catalog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (output / "checksums.sha256").open("w", encoding="utf-8") as handle:
        for card in rows:
            for path in files_by_card[card["card"]]:
                relative = path.relative_to(TASKS)
                handle.write(f"{hash_file(path)}  {relative.as_posix()}\n")
    total = sum(int(row["all_bytes"]) for row in rows)
    payload_total = sum(int(row["payload_bytes"]) for row in rows)
    likely = sum(row["release_status"] == "likely_republishable_review_required" for row in rows)
    readme = "\n".join([
        "# paper-bench task data release staging",
        "",
        f"- Cards inventoried: {len(rows)}",
        f"- Total input bytes: {total}",
        f"- Payload bytes excluding metadata: {payload_total}",
        f"- Cards with CC-BY/CC0 evidence: {likely}",
        "",
        "`catalog.csv` is an inventory, not a redistribution authorization.",
        "Only cards passed with an explicit --cards allow-list are staged under payload/.",
        "The catalog and checksums cover tasks/<domain>/<card>/data only; baseline",
        "submissions and private evaluator material are excluded.",
        "",
    ])
    (output / "README.md").write_text(readme, encoding="utf-8")
    return rows, files_by_card


def hardlink_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def copy_metadata_without_local_paths(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8", errors="replace")
    target.write_text(LOCAL_PATH_PATTERN.sub("<local-path>", text), encoding="utf-8")


def stage_payload(output: Path, selected: set[str], files_by_card: dict[str, list[Path]],
                  rows: list[dict[str, str]]) -> None:
    payload_root = output / "payload"
    if payload_root.exists():
        raise RuntimeError(f"staging directory already exists: {payload_root}")
    payload_root.mkdir(parents=True)
    selected_rows = [row for row in rows if row["card"] in selected]
    with (payload_root / "catalog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(selected_rows)
    checksum_lines = []
    for card in sorted(selected):
        if card not in files_by_card:
            raise RuntimeError(f"unknown card: {card}")
        data_root = TASKS / card / "data"
        for source in files_by_card[card]:
            target = payload_root / card / source.relative_to(data_root)
            if source.name in STAGED_METADATA_NAMES:
                copy_metadata_without_local_paths(source, target)
            elif source.name in METADATA_NAMES:
                continue
            else:
                hardlink_or_copy(source, target)
            checksum_lines.append(
                f"{hash_file(target)}  {target.relative_to(payload_root).as_posix()}"
            )
    (payload_root / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    readme = "\n".join([
        "---",
        "license: cc-by-4.0",
        "tags:",
        "- benchmark",
        "- scientific-computing",
        "- paper-bench",
        "---",
        "",
        "# paper-bench public data mirror: phase 1",
        "",
        "This ModelScope dataset mirrors explicitly selected paper-bench task inputs",
        "with explicit CC BY 4.0 or CC0 evidence in their local source records.",
        "Each task keeps the layout `<domain>/<card_id>/...`, suitable for",
        "`PAPER_BENCH_DATA_ROOT`.",
        "",
        "`catalog.csv` records source evidence and sizes. `checksums.sha256`",
        "covers every staged task file. Source and license records are included",
        "where available; local storage paths in those records are redacted.",
        "`availability` distinguishes complete local payloads from cards that also",
        "reference local external storage. No symbolic links or local-path records",
        "are included in this mirror.",
        "",
        "This is a distribution mirror. It does not contain benchmark answers,",
        "scoring rubrics, baseline submissions, or private evaluation material.",
        "",
    ])
    (payload_root / "README.md").write_text(readme, encoding="utf-8")
    print(f"staged {len(selected)} explicitly selected cards at {payload_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(ROOT / ".paperbench" / "data-release"))
    parser.add_argument("--stage", action="store_true", help="stage only explicitly selected cards")
    parser.add_argument("--cards", nargs="*", default=[], help="domain/card allow-list for --stage")
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    rows, files_by_card = build_catalog(output)
    print(f"wrote catalog and checksums: {output}")
    if args.stage:
        if not args.cards:
            raise SystemExit("--stage requires one or more --cards domain/card values")
        eligible = {
            row["card"]
            for row in rows
            if row["release_status"] == "likely_republishable_review_required"
            and int(row["payload_files"]) > 0
        }
        disallowed = [card for card in args.cards if card not in eligible]
        if disallowed:
            raise SystemExit(
                "refusing to stage cards without CC-BY/CC0 evidence and actual input files: "
                + ", ".join(disallowed)
            )
        stage_payload(output, set(args.cards), files_by_card, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
