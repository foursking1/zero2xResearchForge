#!/usr/bin/env python3
"""Small, dependency-free CLI for using and releasing paper-bench safely.

The repository contains benchmark definitions.  Frozen task data lives outside
Git and is linked into an ignored task-local ``data/`` path only when needed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
CARDS = ROOT / "cards.csv"
REQUIRED_CARD_FILES = ("TASK.md", "PAPER_ANCHOR.md", "SCORE_RUBRIC.md", "CALIBRATION.md")
PRIVATE_CARD_ROOT = ROOT / "evaluation" / "private" / "cards"
INTERNAL_SUBMISSIONS = ROOT / "submissions"
BASELINES = ROOT / "baselines"
LEGACY_TASK_DATA_PATH = re.compile(
    r"(?<![A-Za-z0-9_])(?:[EF]:[\\/]|/mnt/[ef]/)[^\s`'\"<>()\uFF08\uFF09\uFF0C\u3002\uFF1B\uFF1A]*",
    flags=re.IGNORECASE,
)


def load_cards() -> list[dict[str, str]]:
    with CARDS.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_card(card_ref: str) -> tuple[dict[str, str], Path]:
    cards = load_cards()
    if "/" in card_ref:
        domain, card_id = card_ref.strip("/").split("/", 1)
        matches = [row for row in cards if row["domain"] == domain and row["card_id"] == card_id]
    else:
        matches = [row for row in cards if row["card_id"] == card_ref]
    if not matches:
        raise ValueError(f"unknown card: {card_ref}")
    if len(matches) != 1:
        raise ValueError(f"ambiguous card: {card_ref}; use domain/card_id")
    card = matches[0]
    card_dir = TASKS / card["domain"] / card["card_id"]
    if not card_dir.is_dir():
        raise ValueError(f"card is listed but its directory is absent: {card_dir}")
    return card, card_dir


def private_card_dir(card: dict[str, str]) -> Path:
    configured = os.environ.get("PAPER_BENCH_PRIVATE_CARD_ROOT")
    root = Path(configured).expanduser().resolve() if configured else PRIVATE_CARD_ROOT
    return root / card["domain"] / card["card_id"]


def selected_data_dir(card: dict[str, str], args: argparse.Namespace) -> Path:
    if getattr(args, "data_dir", None):
        return Path(args.data_dir).expanduser().resolve()
    data_root = getattr(args, "data_root", None) or os.environ.get("PAPER_BENCH_DATA_ROOT")
    if not data_root:
        raise ValueError("set --data-dir, --data-root, or PAPER_BENCH_DATA_ROOT")
    return (Path(data_root).expanduser() / card["domain"] / card["card_id"]).resolve()


def selected_submission_dir(card: dict[str, str], card_dir: Path, args: argparse.Namespace) -> Path:
    """Return an explicit member submission or the checked-in baseline."""
    configured = getattr(args, "submission", None)
    if configured:
        return Path(configured).expanduser().resolve()
    return BASELINES / card["domain"] / card["card_id"]


def link_data(card: dict[str, str], card_dir: Path, data_dir: Path, replace: bool, dry_run: bool) -> Path:
    if not data_dir.is_dir():
        raise ValueError(f"data directory does not exist: {data_dir}")
    target = card_dir / "data"
    if target.is_symlink():
        existing = target.resolve()
        if existing == data_dir:
            print(f"data link already correct: {target} -> {data_dir}")
            return target
        if not replace:
            raise ValueError(f"data link already points to {existing}; pass --replace to change it")
        if dry_run:
            print(f"would replace data link: {target} -> {data_dir}")
            return target
        target.unlink()
    elif target.exists():
        if target.resolve() == data_dir:
            print(f"data directory already correct: {target}")
            return target
        raise ValueError(f"refusing to replace a real data directory: {target}")
    if dry_run:
        print(f"would create data link: {target} -> {data_dir}")
        return target
    target.symlink_to(data_dir, target_is_directory=True)
    print(f"created ignored data link: {target} -> {data_dir}")
    return target


def command_list(_: argparse.Namespace) -> int:
    for card in load_cards():
        print(f"{card['domain']}/{card['card_id']}\t{card.get('level', '')}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    listed = load_cards()
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for card in listed:
        key = (card["domain"], card["card_id"])
        if key in seen:
            errors.append(f"duplicate cards.csv entry: {key[0]}/{key[1]}")
        seen.add(key)
        card_dir = TASKS / key[0] / key[1]
        for name in REQUIRED_CARD_FILES:
            location = private_card_dir(card) / name if name != "TASK.md" else card_dir / name
            if not location.is_file():
                errors.append(f"missing {name}: {location}")
        if card_dir.is_dir():
            unexpected = sorted(
                entry.name for entry in card_dir.iterdir()
                if entry.name not in {"TASK.md", "data"}
            )
            if unexpected:
                errors.append(
                    f"task directory contains non-task material: {card_dir} ({', '.join(unexpected)})"
                )
        task_file = card_dir / "TASK.md"
        if task_file.is_file():
            task_text = task_file.read_text(encoding="utf-8", errors="replace")
            if LEGACY_TASK_DATA_PATH.search(task_text):
                errors.append(f"legacy local data path in TASK.md: {card_dir}")
        if args.data_root:
            data_dir = Path(args.data_root).expanduser() / key[0] / key[1]
            if not data_dir.is_dir():
                errors.append(f"missing local data: {data_dir}")
    task_dirs = {path.parent for path in TASKS.glob("*/*/TASK.md")}
    unlisted = sorted(str(path.relative_to(TASKS)) for path in task_dirs
                      if (path.parent.name, path.name) not in seen)
    for item in unlisted:
        errors.append(f"task directory absent from cards.csv: {item}")
    if errors:
        print("check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"check passed: {len(listed)} task specs and private evaluation records present")
    return 0


def command_link_data(args: argparse.Namespace) -> int:
    card, card_dir = resolve_card(args.card)
    data_dir = selected_data_dir(card, args)
    link_data(card, card_dir, data_dir, args.replace, args.dry_run)
    return 0


def command_fetch_modelscope_dataset(args: argparse.Namespace, label: str) -> int:
    destination = Path(args.output).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()) and not args.resume:
        raise ValueError(
            f"destination is not empty: {destination}; pass --resume to continue a previous download"
        )
    cli = shutil.which("modelscope")
    if not cli:
        raise RuntimeError("ModelScope CLI is not installed; run: python3 -m pip install -U modelscope")

    # ModelScope changed this command between CLI releases. Detect the local
    # syntax so an organization can use either a current or older approved CLI.
    help_result = subprocess.run(
        [cli, "download", "--help"], capture_output=True, text=True, check=False
    )
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    if "--dataset" in help_text:
        command = [cli, "download", "--dataset", args.repo, "--local_dir", str(destination)]
        worker_flag = "--max_workers"
    else:
        command = [cli, "download", args.repo, "--repo-type", "dataset", "--local-dir", str(destination)]
        worker_flag = "--max-workers"
    revision = getattr(args, "revision", None)
    if revision and "--revision" in help_text:
        command.extend(["--revision", revision])
    if worker_flag in help_text:
        command.extend([worker_flag, str(args.workers)])
    token = os.environ.get("MODELSCOPE_API_TOKEN")
    if token and "--token" in help_text:
        command.extend(["--token", token])
    print(f"downloading ModelScope {label} {args.repo} to {destination}")
    result = subprocess.run(command, cwd=ROOT, check=False).returncode
    if result == 0 and not (destination / "checksums.sha256").is_file():
        print("warning: download completed but checksums.sha256 is absent", file=sys.stderr)
    return result


def command_fetch_data(args: argparse.Namespace) -> int:
    return command_fetch_modelscope_dataset(args, "task data")


def command_fetch_baselines(args: argparse.Namespace) -> int:
    return command_fetch_modelscope_dataset(args, "baseline artifacts")


def command_run(args: argparse.Namespace) -> int:
    card, card_dir = resolve_card(args.card)
    data_dir = selected_data_dir(card, args)
    data_link = link_data(card, card_dir, data_dir, args.replace, args.dry_run)
    submission_dir = selected_submission_dir(card, card_dir, args)
    cwd = submission_dir if args.cwd == "solution" else card_dir
    if not cwd.is_dir():
        raise ValueError(f"working directory does not exist: {cwd}")
    env = dict(os.environ)
    env.update({
        "PAPER_BENCH_ROOT": str(ROOT),
        "PAPER_BENCH_CARD_DIR": str(card_dir),
        "PAPER_BENCH_DATA_DIR": str(data_dir),
        "PAPER_BENCH_DATA_LINK": str(data_link),
        "PAPER_BENCH_SUBMISSION_DIR": str(submission_dir),
    })
    print(f"card: {card['domain']}/{card['card_id']}")
    print(f"cwd: {cwd}")
    print(f"data: {data_dir}")
    print(f"command: {args.command}")
    if args.dry_run:
        return 0
    return subprocess.run(args.command, cwd=cwd, env=env, shell=True, check=False).returncode


def command_init_submission(args: argparse.Namespace) -> int:
    card, card_dir = resolve_card(args.card)
    destination = (
        Path(args.output).expanduser().resolve()
        if args.output
        else INTERNAL_SUBMISSIONS / card["domain"] / card["card_id"]
    )
    if destination.exists() and any(destination.iterdir()) and not args.force:
        raise ValueError(f"submission directory is not empty: {destination}; pass --force to add missing files")
    if args.dry_run:
        print(f"would initialize submission directory: {destination}")
        return 0
    destination.mkdir(parents=True, exist_ok=True)
    readme = destination / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Submission: {card['domain']}/{card['card_id']}\n\n"
            f"Task specification: `{card_dir / 'TASK.md'}`\n\n"
            "Implement and run your solution here. `paperbench.py run` supplies "
            "`PAPER_BENCH_DATA_DIR`, `PAPER_BENCH_CARD_DIR`, and "
            "`PAPER_BENCH_SUBMISSION_DIR`. Add machine-readable evidence such as "
            "`metrics.json`, `claim.md`, or `evidence_table.csv` before judging.\n",
            encoding="utf-8",
        )
    print(f"initialized submission directory: {destination}")
    return 0


def checksum_entries(
    checksum_file: Path, prefix: str | None, allow_external_symlinks: bool
) -> Iterable[tuple[str, Path]]:
    root = checksum_file.parent.resolve()
    normalized_prefix = prefix.strip("/") + "/" if prefix else ""
    with checksum_file.open(encoding="utf-8", errors="strict") as handle:
        for line_number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                expected, relative = line.split(maxsplit=1)
            except ValueError as error:
                raise ValueError(f"invalid checksum entry at {checksum_file}:{line_number}") from error
            relative = relative.lstrip("*").replace("\\", "/")
            if len(expected) != 64 or any(char not in "0123456789abcdefABCDEF" for char in expected):
                raise ValueError(f"invalid SHA-256 at {checksum_file}:{line_number}")
            if prefix and not relative.startswith(normalized_prefix):
                continue
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"checksum path escapes data root: {relative}")
            candidate = root / relative_path
            resolved = candidate.resolve()
            if not allow_external_symlinks and root not in resolved.parents and resolved != root:
                raise ValueError(
                    f"checksum path resolves outside data root: {relative}; "
                    "use --allow-external-symlinks only for trusted maintainer staging"
                )
            yield expected.lower(), candidate


def command_verify_data(args: argparse.Namespace) -> int:
    root = Path(args.data_root).expanduser().resolve()
    checksum_file = root / "checksums.sha256"
    if not checksum_file.is_file():
        raise ValueError(f"missing checksum file: {checksum_file}")
    prefix = None
    if args.card:
        card, _ = resolve_card(args.card)
        prefix = f"{card['domain']}/{card['card_id']}"
    checked = 0
    failures: list[str] = []
    for expected, path in checksum_entries(checksum_file, prefix, args.allow_external_symlinks):
        if args.limit and checked >= args.limit:
            break
        checked += 1
        if not path.is_file():
            failures.append(f"missing: {path}")
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            failures.append(f"checksum mismatch: {path}")
    if not checked:
        raise ValueError("no checksum entries matched the requested scope")
    if failures:
        print(f"data verification failed: {len(failures)}/{checked} file(s) invalid", file=sys.stderr)
        for failure in failures[:20]:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"data verification passed: {checked} file(s)")
    return 0


def command_evaluate(args: argparse.Namespace) -> int:
    card, card_dir = resolve_card(args.card)
    submission = selected_submission_dir(card, card_dir, args)
    if not submission.is_dir():
        raise ValueError(f"submission directory does not exist: {submission}")
    output = Path(args.output).expanduser().resolve() if args.output else submission / "evaluation"
    command = [
        sys.executable,
        str(ROOT / "evaluation" / "judge_submission.py"),
        f"{card['domain']}/{card['card_id']}",
        "--submission",
        str(submission),
        "--output",
        str(output),
    ]
    if args.model:
        command.extend(["--model", args.model])
    if args.dry_run:
        command.append("--dry-run")
    env = dict(os.environ)
    env["PAPER_BENCH_ROOT"] = str(ROOT)
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def command_release(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(ROOT / "tools" / "build_participant_release.py"),
        "--output", args.output,
        "--dataset-repo", args.dataset_repo,
        "--dataset-revision", args.dataset_revision,
    ]
    if args.init_git:
        command.append("--init-git")
    if args.dry_run:
        command.append("--dry-run")
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="subcommand", required=True)

    list_parser = sub.add_parser("list", help="list cards from cards.csv")
    list_parser.set_defaults(func=command_list)

    check_parser = sub.add_parser("check", help="validate the benchmark repository")
    check_parser.add_argument("--data-root", help="also require <root>/<domain>/<card_id> for every card")
    check_parser.set_defaults(func=command_check)

    link_parser = sub.add_parser("link-data", help="link one local frozen data directory into a card")
    link_parser.add_argument("card", help="card_id or domain/card_id")
    link_parser.add_argument("--data-dir", help="exact frozen data directory")
    link_parser.add_argument("--data-root", help="root containing domain/card_id data directories")
    link_parser.add_argument("--replace", action="store_true", help="replace an existing data symlink only")
    link_parser.add_argument("--dry-run", action="store_true")
    link_parser.set_defaults(func=command_link_data)

    fetch_parser = sub.add_parser("fetch-data", help="download the frozen ModelScope data mirror")
    fetch_parser.add_argument("--output", required=True, help="empty directory for <domain>/<card_id>/ data")
    fetch_parser.add_argument(
        "--repo",
        default=os.environ.get("MODELSCOPE_DATASET_REPO", "foursking1/zero2xResearchForge"),
        help="ModelScope dataset repository (default: foursking1/zero2xResearchForge)",
    )
    fetch_parser.add_argument(
        "--revision",
        default=os.environ.get("MODELSCOPE_DATASET_REVISION", "master"),
        help="immutable ModelScope tag or commit (default: MODELSCOPE_DATASET_REVISION or master)",
    )
    fetch_parser.add_argument("--workers", type=int, default=4, help="parallel download workers")
    fetch_parser.add_argument("--resume", action="store_true", help="continue into a non-empty output directory")
    fetch_parser.set_defaults(func=command_fetch_data)

    baseline_parser = sub.add_parser(
        "fetch-baselines", help="download optional historical baseline artifacts from ModelScope"
    )
    baseline_parser.add_argument("--output", required=True, help="empty directory for archived baselines/... outputs")
    baseline_parser.add_argument(
        "--repo",
        default=os.environ.get(
            "MODELSCOPE_BASELINE_ARTIFACTS_REPO", "foursking1/zero2xResearchForge-baselines"
        ),
        help="ModelScope baseline-artifact repository",
    )
    baseline_parser.add_argument(
        "--revision",
        default=os.environ.get("MODELSCOPE_BASELINE_ARTIFACTS_REVISION", "master"),
        help="immutable ModelScope tag or commit (default: MODELSCOPE_BASELINE_ARTIFACTS_REVISION or master)",
    )
    baseline_parser.add_argument("--workers", type=int, default=4, help="parallel download workers")
    baseline_parser.add_argument("--resume", action="store_true", help="continue into a non-empty output directory")
    baseline_parser.set_defaults(func=command_fetch_baselines)

    run_parser = sub.add_parser("run", help="run a task command with local data configured")
    run_parser.add_argument("card", help="card_id or domain/card_id")
    run_parser.add_argument("--command", required=True, help="command to run; see the card's TASK.md")
    run_parser.add_argument("--submission", help="member submission directory; defaults to the card baseline")
    run_parser.add_argument("--data-dir", help="exact frozen data directory")
    run_parser.add_argument("--data-root", help="root containing domain/card_id data directories")
    run_parser.add_argument("--cwd", choices=("card", "solution"), default="solution")
    run_parser.add_argument("--replace", action="store_true", help="replace an existing data symlink only")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.set_defaults(func=command_run)

    init_parser = sub.add_parser("init-submission", help="create an ignored member submission workspace")
    init_parser.add_argument("card", help="card_id or domain/card_id")
    init_parser.add_argument("--output", help="submission directory (default: submissions/<domain>/<card>)")
    init_parser.add_argument("--force", action="store_true", help="add missing scaffold files to a non-empty directory")
    init_parser.add_argument("--dry-run", action="store_true")
    init_parser.set_defaults(func=command_init_submission)

    verify_parser = sub.add_parser("verify-data", help="verify downloaded data against checksums.sha256")
    verify_parser.add_argument("--data-root", required=True, help="root downloaded from ModelScope")
    verify_parser.add_argument("--card", help="verify one domain/card instead of the complete mirror")
    verify_parser.add_argument("--limit", type=int, default=0, help="verify at most this many files (smoke test)")
    verify_parser.add_argument(
        "--allow-external-symlinks",
        action="store_true",
        help="allow trusted maintainer staging payloads whose symlinks target the frozen source",
    )
    verify_parser.set_defaults(func=command_verify_data)

    evaluate_parser = sub.add_parser("evaluate", help="LLM-judge one member submission against private anchors")
    evaluate_parser.add_argument("card", help="card_id or domain/card_id")
    evaluate_parser.add_argument("--submission", help="member submission directory; defaults to the card baseline")
    evaluate_parser.add_argument("--output", help="directory for result.json and report.md (default: <submission>/evaluation)")
    evaluate_parser.add_argument("--model", help="override JUDGE_MODEL for this evaluation")
    evaluate_parser.add_argument("--dry-run", action="store_true", help="validate the submission without calling the LLM")
    evaluate_parser.set_defaults(func=command_evaluate)

    release_parser = sub.add_parser("release", help="create a new answer-free participant repository")
    release_parser.add_argument("--output", required=True, help="new or empty participant-release directory")
    release_parser.add_argument(
        "--dataset-repo", default=os.environ.get("MODELSCOPE_DATASET_REPO", "foursking1/zero2xResearchForge"),
        help="ModelScope dataset repository",
    )
    release_parser.add_argument(
        "--dataset-revision", default=os.environ.get("MODELSCOPE_DATASET_REVISION"),
        help="required immutable ModelScope tag or commit",
    )
    release_parser.add_argument("--init-git", action="store_true", help="initialize a fresh Git repository in output")
    release_parser.add_argument("--dry-run", action="store_true")
    release_parser.set_defaults(func=command_release)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.subcommand == "release" and not args.dataset_revision:
            raise ValueError("--dataset-revision or MODELSCOPE_DATASET_REVISION is required")
        return args.func(args)
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
