#!/usr/bin/env python3
"""Participant-only CLI for the answer-free PaperBench release."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"


def load_catalog() -> dict:
    with CATALOG.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_card(reference: str) -> dict:
    catalog = load_catalog()
    normalized = reference.strip("/")
    matches = [
        card for card in catalog["cards"]
        if normalized in {card["task_id"], f"{card['domain']}/{card['task_id']}"}
    ]
    if len(matches) != 1:
        raise ValueError(f"unknown or ambiguous task: {reference}; use domain/task_id")
    return matches[0]


def data_dir(card: dict, args: argparse.Namespace) -> Path:
    if getattr(args, "data_dir", None):
        return Path(args.data_dir).expanduser().resolve()
    root = getattr(args, "data_root", None) or os.environ.get("PAPER_BENCH_DATA_ROOT")
    if not root:
        raise ValueError("set --data-dir, --data-root, or PAPER_BENCH_DATA_ROOT")
    return (Path(root).expanduser() / card["domain"] / card["task_id"]).resolve()


def command_list(_: argparse.Namespace) -> int:
    for card in load_catalog()["cards"]:
        print(f"{card['domain']}/{card['task_id']}")
    return 0


def command_fetch_data(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    destination = Path(args.output).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()) and not args.resume:
        raise ValueError("download destination is not empty; pass --resume to continue")
    cli = shutil.which("modelscope")
    if not cli:
        raise RuntimeError("install ModelScope first: python3 -m pip install -U modelscope")
    help_result = subprocess.run([cli, "download", "--help"], capture_output=True, text=True, check=False)
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    if "--dataset" in help_text:
        command = [cli, "download", "--dataset", catalog["dataset"]["repo"], "--local_dir", str(destination)]
        worker_flag = "--max_workers"
    else:
        command = [cli, "download", catalog["dataset"]["repo"], "--repo-type", "dataset", "--local-dir", str(destination)]
        worker_flag = "--max-workers"
    if "--revision" in help_text:
        command.extend(["--revision", catalog["dataset"]["revision"]])
    if worker_flag in help_text:
        command.extend([worker_flag, str(args.workers)])
    print(f"downloading {catalog['dataset']['repo']}@{catalog['dataset']['revision']} to {destination}")
    if args.dry_run:
        print("command:", " ".join(command))
        return 0
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def command_verify_data(args: argparse.Namespace) -> int:
    root = Path(args.data_root).expanduser().resolve()
    checksums = root / "checksums.sha256"
    if not checksums.is_file():
        raise ValueError(f"missing checksum inventory: {checksums}")
    prefix = ""
    if args.card:
        card = resolve_card(args.card)
        prefix = f"{card['domain']}/{card['task_id']}/"
    checked = 0
    failures: list[str] = []
    for raw in checksums.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split(maxsplit=1)
        relative = relative.lstrip("*").replace("\\", "/")
        if prefix and not relative.startswith(prefix):
            continue
        path = root / relative
        checked += 1
        if not path.is_file():
            failures.append(f"missing: {relative}")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected.lower():
            failures.append(f"checksum mismatch: {relative}")
    if not checked:
        raise ValueError("no checksum entries matched the requested scope")
    if failures:
        print(f"data verification failed: {len(failures)}/{checked}", file=sys.stderr)
        for failure in failures[:20]:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"data verification passed: {checked} files")
    return 0


def command_init_submission(args: argparse.Namespace) -> int:
    card = resolve_card(args.card)
    destination = Path(args.output).expanduser().resolve() if args.output else (
        ROOT / "submissions" / card["domain"] / card["task_id"]
    )
    if destination.exists() and any(destination.iterdir()) and not args.force:
        raise ValueError("submission directory is not empty; pass --force to retain its contents")
    if args.dry_run:
        print(f"would initialize {destination}")
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    readme = destination / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Submission: {card['domain']}/{card['task_id']}\n\n"
            "Use the paper and frozen data to produce your own evidence. The required "
            "deliverables are listed in SUBMISSION_CONTRACT.md.\n",
            encoding="utf-8",
        )
    print(f"initialized submission: {destination}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    card = resolve_card(args.card)
    input_dir = data_dir(card, args)
    submission = Path(args.submission).expanduser().resolve()
    if not input_dir.is_dir():
        raise ValueError(f"data directory does not exist: {input_dir}")
    if not submission.is_dir():
        raise ValueError(f"submission directory does not exist: {submission}")
    task_dir = ROOT / "tasks" / card["domain"] / card["task_id"]
    env = dict(os.environ)
    env.update({
        "PAPER_BENCH_ROOT": str(ROOT),
        "PAPER_BENCH_TASK_DIR": str(task_dir),
        "PAPER_BENCH_DATA_ROOT": str(input_dir.parent.parent),
        "PAPER_BENCH_DATA_DIR": str(input_dir),
        "PAPER_BENCH_SUBMISSION_DIR": str(submission),
    })
    print(f"task: {card['domain']}/{card['task_id']}")
    print(f"data: {input_dir}")
    print(f"submission: {submission}")
    if args.dry_run:
        return 0
    return subprocess.run(args.command, cwd=submission, env=env, shell=True, check=False).returncode


def command_fetch_paper(args: argparse.Namespace) -> int:
    card = resolve_card(args.card)
    included = card["paper"].get("included_file")
    task_dir = ROOT / "tasks" / card["domain"] / card["task_id"]
    if included:
        bundled = task_dir / included["path"]
        if not bundled.is_file():
            raise RuntimeError(f"bundled paper is missing: {bundled}")
        if not args.output:
            print(f"bundled paper: {bundled}")
            return 0
        output = Path(args.output).expanduser().resolve()
        if output.exists() and not args.force:
            raise ValueError(f"paper already exists: {output}; pass --force to replace it")
        if args.dry_run:
            print(f"would copy bundled paper {bundled} to {output}")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundled, output)
        print(f"copied bundled paper: {output}")
        return 0
    url = card["paper"].get("pdf_url")
    if not url:
        article = card["paper"].get("article_url", "the cited publisher")
        raise RuntimeError(f"this task has no verified PDF URL; obtain it through {article}")
    output = Path(args.output).expanduser().resolve() if args.output else (
        ROOT / "papers" / card["domain"] / card["task_id"] / "paper.pdf"
    )
    if output.exists() and not args.force:
        raise ValueError(f"paper already exists: {output}; pass --force to replace it")
    if args.dry_run:
        print(f"would download {url} to {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, output)
    print(f"downloaded paper: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list", help="list task IDs")
    list_parser.set_defaults(func=command_list)
    fetch = sub.add_parser("fetch-data", help="download the complete frozen ModelScope mirror")
    fetch.add_argument("--output", required=True)
    fetch.add_argument("--workers", type=int, default=4)
    fetch.add_argument("--resume", action="store_true")
    fetch.add_argument("--dry-run", action="store_true")
    fetch.set_defaults(func=command_fetch_data)
    verify = sub.add_parser("verify-data", help="verify ModelScope checksums")
    verify.add_argument("--data-root", required=True)
    verify.add_argument("--card")
    verify.set_defaults(func=command_verify_data)
    init = sub.add_parser("init-submission", help="create a participant workspace")
    init.add_argument("card")
    init.add_argument("--output")
    init.add_argument("--force", action="store_true")
    init.add_argument("--dry-run", action="store_true")
    init.set_defaults(func=command_init_submission)
    run = sub.add_parser("run", help="run a participant command with frozen-data variables")
    run.add_argument("card")
    run.add_argument("--submission", required=True)
    run.add_argument("--command", required=True)
    run.add_argument("--data-root")
    run.add_argument("--data-dir")
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(func=command_run)
    paper = sub.add_parser("fetch-paper", help="download an official paper PDF when a URL is available")
    paper.add_argument("card")
    paper.add_argument("--output")
    paper.add_argument("--force", action="store_true")
    paper.add_argument("--dry-run", action="store_true")
    paper.set_defaults(func=command_fetch_paper)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
