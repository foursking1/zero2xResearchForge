#!/usr/bin/env python3
"""Generate an answer-free participant release from the maintainer repository.

The output is intentionally a new tree. Publish it through a fresh Git history;
never expose this maintainer repository or its history to participants.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards.csv"
CLI_TEMPLATE = ROOT / "templates" / "participant" / "participantbench.py"
DEFAULT_DATASET = "foursking1/zero2xResearchForge"
ARXIV_ID = re.compile(r"^(?P<identifier>\d{4}\.\d{4,5})(?:v\d+)?(?:_|$)")
PAPER_REGISTRY = {
    "08_tapley_2004": {
        "source": "DOI",
        "identifier": "10.1126/science.1099192",
        "article_url": "https://doi.org/10.1126/science.1099192",
    },
    "bensen_2007": {
        "source": "DOI",
        "identifier": "10.1111/j.1365-246X.2007.03374.x",
        "article_url": "https://doi.org/10.1111/j.1365-246X.2007.03374.x",
        "pdf_url": "https://noise.earth.utah.edu/2.pdf",
    },
    "bonjean_2002": {
        "source": "DOI",
        "identifier": "10.1175/1520-0485(2002)032<2938:DMAAOT>2.0.CO;2",
        "article_url": "https://doi.org/10.1175/1520-0485%282002%29032%3C2938%3ADMAAOT%3E2.0.CO%3B2",
    },
    "gehlen_2019": {
        "source": "DOI",
        "identifier": "10.3389/fmars.2019.00579",
        "article_url": "https://doi.org/10.3389/fmars.2019.00579",
    },
    "pages2k_2019": {
        "source": "DOI",
        "identifier": "10.1038/s41561-019-0400-0",
        "article_url": "https://doi.org/10.1038/s41561-019-0400-0",
        "pdf_url": "https://www.nature.com/articles/s41561-019-0400-0.pdf",
    },
    "wong_2020": {
        "source": "DOI",
        "identifier": "10.3389/fmars.2020.00024",
        "article_url": "https://doi.org/10.3389/fmars.2020.00024",
        "pdf_url": "https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2020.00024/pdf",
    },
}
LOCAL_PAPER_CANDIDATES = {
    "08_tapley_2004": (
        "papers/10.1126_science.1099192.pdf",
        "08_tapley_2004/10.1126_science.1099192.pdf",
    ),
    "bensen_2007": ("papers/10.1111_j.1365-246X.2007.03374.x.pdf",),
    "bonjean_2002": ("papers/10.1175_1520-0485_2002_032_2938_DRSOTC_2.0.CO_2.pdf",),
    "gehlen_2019": (
        "papers/10.3389_fmars.2019.00579.pdf",
        "gehlen_2019/10.3389_fmars.2019.00579.pdf",
    ),
    "pages2k_2019": (
        "papers/10.1038_s41561-019-0400-0.pdf",
        "pages2k_2019/10.1038_s41561-019-0400-0.pdf",
    ),
    "wong_2020": ("wong_2020/fmars-2020-00024.pdf",),
}
FORBIDDEN_PARTS = {
    "baselines", "evaluations", "evaluation", "results", "private",
    "paper_anchor.md", "score_rubric.md", "calibration.md", "task.md",
}


def load_cards() -> list[dict[str, str]]:
    with CARDS.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def paper_reference(task_id: str) -> dict[str, str]:
    if task_id in PAPER_REGISTRY:
        return dict(PAPER_REGISTRY[task_id])
    match = ARXIV_ID.match(task_id)
    if not match:
        raise ValueError(f"task lacks an approved paper reference: {task_id}")
    identifier = match.group("identifier")
    return {
        "source": "arXiv",
        "identifier": identifier,
        "abstract_url": f"https://arxiv.org/abs/{identifier}",
        "pdf_url": f"https://arxiv.org/pdf/{identifier}.pdf",
    }


def task_manifest(card: dict[str, str], dataset_repo: str, dataset_revision: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "task_id": card["card_id"],
        "domain": card["domain"],
        "paper": paper_reference(card["card_id"]),
        "data": {
            "provider": "ModelScope",
            "repo": dataset_repo,
            "revision": dataset_revision,
            "relative_path": f"{card['domain']}/{card['card_id']}",
            "checksum_inventory": "checksums.sha256",
        },
        "submission_contract": "../../../SUBMISSION_CONTRACT.md",
    }


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_paper_candidates(domain: str, task_id: str) -> tuple[str, ...]:
    """Known cache locations for the curated local paper mirror.

    This is deliberately an allowlist instead of a recursive filename search: a
    task package must never pick up a generated figure, appendix, or unrelated
    PDF merely because its name resembles a card ID.
    """
    task_copy = f"tasks/{domain}/{task_id}/paper.pdf"
    if task_id in LOCAL_PAPER_CANDIDATES:
        return (task_copy, *LOCAL_PAPER_CANDIDATES[task_id])
    match = ARXIV_ID.match(task_id)
    if not match:
        return ()
    identifier = match.group("identifier")
    return (
        task_copy,
        f"candidate-papers/{domain}/{identifier}.pdf",
        f"{task_id}/arxiv_{task_id}.pdf",
        f"{task_id}/arxiv_{task_id}_original.pdf",
        f"{task_id}/{task_id}.pdf",
        f"materials/_candidate_pdfs/{identifier}.pdf",
        f"_tmp_{identifier}.pdf",
        f"earth_tmp/{identifier}.pdf",
    )


def find_local_paper(source_root: Path, domain: str, task_id: str) -> Path | None:
    for relative in local_paper_candidates(domain, task_id):
        candidate = source_root / relative
        if candidate.is_file():
            with candidate.open("rb") as handle:
                if handle.read(5) != b"%PDF-":
                    raise ValueError(f"local paper is not a PDF: {candidate}")
            return candidate
    return None


def include_local_paper(task_dir: Path, manifest: dict[str, Any], source: Path) -> None:
    destination = task_dir / "paper.pdf"
    shutil.copy2(source, destination)
    manifest["paper"]["included_file"] = {
        "path": "paper.pdf",
        "sha256": digest_file(destination),
        "bytes": destination.stat().st_size,
    }


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def readme(dataset_repo: str, dataset_revision: str, bundled_papers: int) -> str:
    return f"""# PaperBench Participant Kit

This is the participant-facing release. It contains no answer key, reference
solution, historical score, private anchor, scoring rubric, or local evaluator.

## Start Here

Download the frozen inputs before opening a submission workspace:

```bash
python3 -m pip install -U modelscope
modelscope login --token <organization-token>
python3 participantbench.py fetch-data --output /path/to/paper-bench-data
export PAPER_BENCH_DATA_ROOT=/path/to/paper-bench-data
python3 participantbench.py verify-data --data-root "$PAPER_BENCH_DATA_ROOT"
```

This release is pinned to `{dataset_repo}@{dataset_revision}`. Do not replace
the frozen data with another revision.

```bash
python3 participantbench.py fetch-paper astro/1903.02557_dash_supernova_class
python3 participantbench.py init-submission astro/1903.02557_dash_supernova_class
python3 participantbench.py run astro/1903.02557_dash_supernova_class \\
  --submission submissions/astro/1903.02557_dash_supernova_class \\
  --command 'python run.py'
```

Submit the resulting directory through the organization submission channel. The
private judge runs only in maintainer-controlled infrastructure.

## Paper Access

{bundled_papers} task cards include `paper.pdf`, copied from the operator's
curated local paper mirror and recorded with a SHA-256 digest in `paper.json`.
The remaining cards include an official paper page and, where verified, an
official or author-hosted PDF URL. If a card has no bundled file or PDF URL, use
its publisher page with the organization's library access.

Only include PDFs when the release operator is authorized to redistribute them
to the intended participants. Binary papers can make a Git repository large;
use the organization's ModelScope release or Git LFS when publishing this kit.

## Security Boundary

Do not add anchors, rubrics, reference solutions, historical evaluations, or
judge credentials to this repository. It must be created and published with a
fresh Git history, never by granting participants access to the maintainer repo.
"""


SUBMISSION_CONTRACT = """# Submission Contract

Each submission is an independent directory. Include these artifacts when they
apply to the paper reproduction:

- `claim.md`: concise statement of what your run establishes and its limits.
- `report.md`: method, environment, data preparation, and interpretation.
- `metrics.json`: machine-readable measured metrics.
- `evidence_table.csv`: metric-to-evidence mapping.
- `code/`: source code and a runnable entry point.

Use `PAPER_BENCH_DATA_DIR` for the downloaded task data and write all outputs
inside your submission directory. Do not submit downloaded source data, API keys,
or model weights unless the organization explicitly requests them.
"""


SECURITY = """# Release Security

This participant kit intentionally excludes private scoring material. It is not
safe to publish the maintainer repository, even after deleting files, because
Git history can retain prior anchors and reference submissions.

Create a new repository from this generated directory, then commit only this
directory. Keep the maintainer repository and judge endpoint access restricted.
"""


def verify_tree(output: Path) -> None:
    forbidden: list[str] = []
    for path in output.rglob("*"):
        relative = path.relative_to(output)
        if any(part.lower() in FORBIDDEN_PARTS for part in relative.parts):
            forbidden.append(relative.as_posix())
    if forbidden:
        raise RuntimeError(f"participant release contains forbidden paths: {forbidden[:5]}")
    for task in output.glob("tasks/*/*/task.json"):
        content = task.read_text(encoding="utf-8")
        for marker in ("PAPER_ANCHOR", "SCORE_RUBRIC", "EVAL_REPORT", "agent_solution"):
            if marker in content:
                raise RuntimeError(f"participant task leaks marker {marker}: {task}")


def write_checksums(output: Path) -> None:
    entries = []
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        entries.append(f"{digest.hexdigest()}  {path.relative_to(output).as_posix()}")
    write_text(output / "SHA256SUMS", "\n".join(entries) + "\n")


def build(
    output: Path,
    dataset_repo: str,
    dataset_revision: str,
    init_git: bool,
    paper_source: Path | None,
) -> int:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    cards = load_cards()
    manifests = [task_manifest(card, dataset_repo, dataset_revision) for card in cards]
    bundled_papers = 0
    for manifest in manifests:
        task_dir = output / "tasks" / manifest["domain"] / manifest["task_id"]
        task_dir.mkdir(parents=True, exist_ok=True)
        if paper_source:
            source = find_local_paper(paper_source, manifest["domain"], manifest["task_id"])
            if source:
                include_local_paper(task_dir, manifest, source)
                bundled_papers += 1
        write_json(task_dir / "task.json", manifest)
        write_json(task_dir / "paper.json", manifest["paper"])
    write_json(output / "catalog.json", {"schema_version": 1, "dataset": {
        "provider": "ModelScope", "repo": dataset_repo, "revision": dataset_revision,
    }, "cards": manifests})
    shutil_target = output / "participantbench.py"
    shutil_target.write_text(CLI_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    shutil_target.chmod(0o755)
    write_text(output / "README.md", readme(dataset_repo, dataset_revision, bundled_papers))
    write_text(output / "SUBMISSION_CONTRACT.md", SUBMISSION_CONTRACT)
    write_text(output / "SECURITY.md", SECURITY)
    write_text(output / ".gitignore", "submissions/\npapers/\n__pycache__/\n")
    verify_tree(output)
    write_checksums(output)
    if init_git:
        subprocess.run(["git", "init", "-b", "main"], cwd=output, check=True)
    return bundled_papers


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new or empty participant-release directory")
    parser.add_argument("--dataset-repo", default=DEFAULT_DATASET)
    parser.add_argument(
        "--dataset-revision", default=os.environ.get("MODELSCOPE_DATASET_REVISION"),
        help="required immutable ModelScope tag or commit",
    )
    parser.add_argument("--init-git", action="store_true", help="initialize a fresh Git repository in output")
    parser.add_argument(
        "--paper-source",
        help="curated local paper mirror; copy only allowlisted, validated PDFs into matching cards",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dataset_revision:
        parser.error("--dataset-revision or MODELSCOPE_DATASET_REVISION is required")
    output = Path(args.output).expanduser().resolve()
    paper_source = Path(args.paper_source).expanduser().resolve() if args.paper_source else None
    if paper_source and not paper_source.is_dir():
        parser.error(f"--paper-source is not a directory: {paper_source}")
    cards = load_cards()
    if args.dry_run:
        print(f"would generate {len(cards)} answer-free task cards in {output}")
        print(f"dataset: {args.dataset_repo}@{args.dataset_revision}")
        return 0
    try:
        bundled_papers = build(output, args.dataset_repo, args.dataset_revision, args.init_git, paper_source)
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"generated {len(cards)} answer-free task cards ({bundled_papers} bundled papers): {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
