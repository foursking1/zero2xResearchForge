# Maintainer Runbook

This is the supported path for authorized maintainers. Both the maintainer GitHub
repository and the `foursking1/zero2xResearchForge` ModelScope dataset may be
private. Access to one does not grant access to the other: an administrator must
grant both explicitly.

## One-Time Setup

```bash
git clone <organization-private-github-url> paper-bench
cd paper-bench
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r requirements-internal.txt

# Authenticate with the member's own ModelScope token. Do not share a token or
# add it to a committed file.
modelscope login --token <member-token>
# The administrator should publish an immutable ModelScope tag or commit and
# distribute its value as MODELSCOPE_DATASET_REVISION.
export MODELSCOPE_DATASET_REVISION=<approved-release-tag-or-commit>
python3 paperbench.py fetch-data --output /data/paper-bench
export PAPER_BENCH_DATA_ROOT=/data/paper-bench
```

The full mirror is approximately 73.6 GB. Reserve additional working space for
the task and its generated artifacts. A successful download contains
`checksums.sha256` at its root.

Validate the directory layout once and checksum a card before starting work:

```bash
python3 paperbench.py check --data-root "$PAPER_BENCH_DATA_ROOT"
python3 paperbench.py verify-data --data-root "$PAPER_BENCH_DATA_ROOT" \
  --card astro/1903.02557_dash_supernova_class
```

Run `verify-data` without `--card` to check the whole mirror. It reads all input
files and can take a substantial amount of time.

## Run A Submission

Each card is a research task, so the member provides the task implementation and
its task-specific environment. The benchmark owns data attachment, a stable
working directory, and the evaluation contract; it does not claim that 125
different scientific software stacks share one dependency lock.

```bash
python3 paperbench.py init-submission astro/1903.02557_dash_supernova_class

# Put code and task outputs in submissions/astro/1903.02557_dash_supernova_class.
# Install any dependencies required by that implementation, then run it:
python3 paperbench.py run astro/1903.02557_dash_supernova_class \
  --submission submissions/astro/1903.02557_dash_supernova_class \
  --data-root "$PAPER_BENCH_DATA_ROOT" \
  --command 'python run.py'
```

The command receives these environment variables:

| Variable | Meaning |
|---|---|
| `PAPER_BENCH_ROOT` | repository root |
| `PAPER_BENCH_CARD_DIR` | task definition (`TASK.md`) only |
| `PAPER_BENCH_DATA_DIR` | immutable downloaded data for this card |
| `PAPER_BENCH_DATA_LINK` | ignored `tasks/<domain>/<card>/data` compatibility link |
| `PAPER_BENCH_SUBMISSION_DIR` | member submission directory |

Do not use historical `F:/...` or `E:/...` paths from older task notes. New
code must use `PAPER_BENCH_DATA_DIR`.

For an evaluation to be meaningful, the submission needs machine-readable
evidence such as `metrics.json`, `claim.md`, or `evidence_table.csv`, in addition
to code and a human-readable report.

## Judge A Submission

The canonical judge is available only to authorized maintainers because it reads
private paper anchors and rubrics. It uses an OpenAI-compatible endpoint; obtain
the endpoint and key from the organization secret manager, never from Git.

The task specification is read from `tasks/<domain>/<card>/TASK.md`; private
anchor, rubric, and calibration files are read from
`evaluation/private/cards/<domain>/<card>/`. For a separately mounted private
store, set `PAPER_BENCH_PRIVATE_CARD_ROOT` to its `cards/` directory before
running the judge.

```bash
cp .env.example .env
# Set JUDGE_API_URL, JUDGE_API_KEY, and JUDGE_MODEL in the ignored .env.
set -a; . ./.env; set +a

python3 paperbench.py evaluate astro/1903.02557_dash_supernova_class \
  --submission submissions/astro/1903.02557_dash_supernova_class
```

The result is written to the ignored
`submissions/<domain>/<card>/evaluation/result.json` and `report.md`. Validate a
submission without calling an LLM or consuming an API quota with:

```bash
python3 paperbench.py evaluate astro/1903.02557_dash_supernova_class \
  --submission submissions/astro/1903.02557_dash_supernova_class --dry-run
```

## Maintainer Operations

`evaluation/judge_eval105_v7.py` and `evaluation/judge_v7_full.py` evaluate the
checked-in `baselines/<domain>/<card>/` trees and write centralized historical
reports under `evaluations/v7/`. They are maintainer tools, not the member
submission interface. Use
`paperbench.py evaluate` for member work so baselines and shared results remain
unchanged.
