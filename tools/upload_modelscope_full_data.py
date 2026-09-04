#!/usr/bin/env python3
"""Reliably upload a prepared PaperBench ModelScope mirror in small batches.

The ModelScope REST commit endpoint can time out for very large file-operation
batches even after accepting the commit. This tool stages small symlinked groups,
checks the remote SHA-256 after each group, and can be rerun safely.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import sys
import time

from modelscope_hub import HubApi
from modelscope_hub import _upload


# The SDK's dataset path normally chooses LFS solely by filename suffix. Frozen
# scientific inputs also include small .dat/.csv/.txt files, which Git may treat
# as text and normalize. Replace that suffix heuristic for this release tool.
def _always_lfs(_: str | Path, __: int, ___: str) -> bool:
    return True


_upload._is_lfs = _always_lfs


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAYLOAD = ROOT / ".paperbench" / "modelscope-full" / "payload"
DEFAULT_REPO = "foursking1/zero2xResearchForge"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def expected_hashes(payload: Path) -> dict[str, str]:
    inventory = payload / "data_inventory.csv"
    if not inventory.is_file():
        raise ValueError(f"missing payload inventory: {inventory}")
    values: dict[str, str] = {}
    with inventory.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            target = row["target_path"]
            checksum = row["payload_sha256"]
            if not target or not checksum:
                raise ValueError(f"invalid inventory row for {target!r}")
            values[target] = checksum.lower()
    for name in (".gitattributes", "README.md", "checksums.sha256", "data_inventory.csv"):
        values[name] = digest(payload / name)
    return values


def remote_hashes(api: HubApi, repo: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in api.list_repo_files(repo, repo_type="dataset", recursive=True):
        if item.type != "blob" or not item.sha256:
            continue
        values[item.path] = item.sha256.lower()
    return values


def stage_group(payload: Path, stage_root: Path, paths: list[str]) -> Path:
    batch_key = hashlib.sha256("\0".join(paths).encode("utf-8")).hexdigest()[:16]
    stage = stage_root / batch_key
    if stage.exists():
        for relative in paths:
            if not (stage / relative).is_file():
                raise RuntimeError(f"incomplete existing batch staging: {stage}")
        return stage
    for relative in paths:
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(payload / relative)
    return stage


def chunks(values: list[str], size: int):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", default=str(DEFAULT_PAYLOAD))
    parser.add_argument("--repo", default=os.environ.get("MODELSCOPE_DATASET_REPO", DEFAULT_REPO))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--commit-prefix", default="Upload PaperBench dataset")
    parser.add_argument("--limit", type=int, help="upload at most this many batches")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be positive")
    if args.workers < 1:
        raise SystemExit("--workers must be positive")
    token = os.environ.get("MODELSCOPE_API_TOKEN")
    payload = Path(args.payload).expanduser().resolve()
    if not payload.is_dir():
        raise SystemExit(f"payload directory does not exist: {payload}")
    expected = expected_hashes(payload)
    stage_root = payload.parent / "upload-batches"
    # HubApi also supports a prior `modelscope login` session, so maintainers do
    # not need to expose a token through the process environment.
    api = HubApi(token=token) if token else HubApi()
    remote = remote_hashes(api, args.repo)
    pending = sorted(path for path, checksum in expected.items() if remote.get(path) != checksum)
    print(f"payload files={len(expected)} remote blobs={len(remote)} pending={len(pending)}")
    if not pending:
        return 0
    if args.dry_run:
        print("first pending paths:")
        for path in pending[:10]:
            print(path)
        return 0

    for index, group in enumerate(chunks(pending, args.batch_size), start=1):
        if args.limit and index > args.limit:
            break
        stage = stage_group(payload, stage_root, group)
        print(f"batch {index}: {len(group)} files")
        try:
            api.upload_folder(
                args.repo,
                repo_type="dataset",
                folder_path=stage,
                commit_message=f"{args.commit_prefix} batch {index}",
                max_workers=args.workers,
                # Remote hash verification is the resume mechanism. Do not let
                # a stale local cache skip a file whose previous commit timed out.
                use_cache=False,
                disable_tqdm=True,
                sync_remote_repo=False,
            )
        except Exception as error:
            # A server-side commit can finish after the client write times out.
            confirmed = remote_hashes(api, args.repo)
            if all(confirmed.get(path) == expected[path] for path in group):
                print(f"batch {index}: accepted despite client error: {error}")
                remote = confirmed
                continue
            print(f"batch {index}: not confirmed: {error}", file=sys.stderr)
            return 1
        unconfirmed: list[str] = group
        for attempt in range(4):
            remote = remote_hashes(api, args.repo)
            unconfirmed = [path for path in group if remote.get(path) != expected[path]]
            if not unconfirmed:
                break
            if attempt < 3:
                time.sleep(5)
        if unconfirmed and len(unconfirmed) > 1:
            print(f"batch {index}: retrying {len(unconfirmed)} unconfirmed paths in groups of 16")
            for retry_index, retry_group in enumerate(chunks(unconfirmed, 16), start=1):
                retry_stage = stage_group(payload, stage_root, retry_group)
                api.upload_folder(
                    args.repo,
                    repo_type="dataset",
                    folder_path=retry_stage,
                    commit_message=f"Retry {args.commit_prefix.lower()} {index}.{retry_index}",
                    max_workers=args.workers,
                    use_cache=False,
                    disable_tqdm=True,
                    sync_remote_repo=False,
                )
            for attempt in range(4):
                remote = remote_hashes(api, args.repo)
                unconfirmed = [path for path in group if remote.get(path) != expected[path]]
                if not unconfirmed:
                    break
                if attempt < 3:
                    time.sleep(5)
        if unconfirmed:
            print(
                f"batch {index}: commit accepted; deferring verification of "
                f"{len(unconfirmed)} asynchronously indexed files"
            )
            continue
        print(f"batch {index}: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
