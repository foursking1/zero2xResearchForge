# Release Guide

This repository is the private maintainer source for paper-bench. It contains
both public task definitions and private evaluator material. Do not publish it
as a GitHub repository or a data archive unchanged.

## Participant Package

Build a new participant repository only after the ModelScope dataset has an
immutable tag or commit. Do not use a moving branch such as `master` as the
published revision.

```bash
export MODELSCOPE_DATASET_REVISION=<approved-release-tag-or-commit>
python3 paperbench.py release \
  --output ../paper-bench-participant \
  --dataset-revision "$MODELSCOPE_DATASET_REVISION" \
  --init-git
```

The output directory is a new Git repository with no commit. Inspect it, commit
only that directory, and push it to the participant repository. Never publish
this maintainer repository, a clone of it, or an archive created from its Git
history.

The kit contains only task ID, official paper reference, fixed ModelScope input
location, and submission contract. It deliberately excludes `TASK.md`, all
anchors and rubrics, `baselines/`, `evaluations/`, evaluator code, evaluation
outputs, and historical results. Participants obtain paper originals from the
official reference in each card when needed.

Keep the private repository and its evaluator on infrastructure controlled by the
benchmark maintainers. Participants download the full frozen data mirror before
work begins, submit a solution bundle, and the private evaluator grades that
bundle. The participant kit has no local `evaluate` command.

## Data release

Raw and derived task data are not Git content. Publish each dataset with an
immutable release identifier, source license, checksum, and a small data manifest.
Host the data in a data repository or object store; the benchmark repository should
only track the manifest and retrieval instructions. See `DATA.md` for the required
local layout and the commands participants use to attach data.

Before announcing a release, record the selected immutable ModelScope revision,
access policy, source licenses, and checksum inventory in the release record.
The generator writes that revision into every participant card and requires the
participant to verify the downloaded `checksums.sha256` inventory.

## Private evaluation

Semantic grading is performed by an LLM judge and therefore needs a model endpoint
and API key in the private evaluator environment. Model configuration belongs in an
ignored `.env` file or deployment secret store. Copy `.env.example` and set
`JUDGE_API_URL`, `JUDGE_API_KEY`, and `JUDGE_MODEL`; never commit credentials.

The LLM judge assesses a submitted solution against `PAPER_ANCHOR.md`. Execution
of a participant command does not itself require an LLM. They are separate stages:
the execution environment provides the frozen data and dependencies, then the
private judge evaluates the resulting evidence.
