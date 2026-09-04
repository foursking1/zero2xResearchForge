# paper-bench

A scientific-paper reproduction and verification benchmark. This is the private
maintainer repository: it includes task specifications, frozen-input references,
and the private ground truth used for organization-internal grading.

This repository is distributed to organization members as a private GitHub
repository. The frozen data lives in the separate private ModelScope dataset
`foursking1/zero2xResearchForge`; members need access to both repositories.

## Structure

```text
paper-bench/
  tasks/<domain>/<card_id>/
    TASK.md              participant task specification
  evaluation/private/cards/<domain>/<card_id>/
    PAPER_ANCHOR.md      maintainer-only paper truth for the judge
    SCORE_RUBRIC.md      maintainer-only scoring rubric
    CALIBRATION.md       maintainer-only calibration notes
  baselines/<domain>/<card_id>/      checked-in historical agent submission
  evaluations/v*/<domain>/<card_id>/ centralized historical judge report
  cards.csv              125-card canonical manifest
  evaluation/            organization-private LLM evaluation pipeline
  results/               shared baseline evaluation outputs
  submissions/           ignored member workspaces and evaluation outputs
  paperbench.py          member data, execution, and evaluation CLI
```

The benchmark covers five domains: `earth`, `astro`, `cs`, `biomed`, and
`materials`. Difficulty labels are `L1` and `L2`.

`tasks/` is deliberately free of private grading files. The private evaluation
material is a logical boundary within this maintainer repository; participants
must receive the separately generated Participant Kit, never this repository or
its history.

## Organization Quick Start

The raw data, checkpoints, and generated arrays are deliberately not Git
content. Authenticate to ModelScope with an organization-authorized account,
then download the complete frozen task-input mirror to an empty directory:

```bash
python3 -m pip install -r requirements-internal.txt
modelscope login --token <member-token>
# Use the immutable ModelScope tag or commit distributed by the administrator.
export MODELSCOPE_DATASET_REVISION=<approved-release-tag-or-commit>
python3 paperbench.py fetch-data --output /mnt/d/paper-bench-data
export PAPER_BENCH_DATA_ROOT=/mnt/d/paper-bench-data
python3 paperbench.py check --data-root "$PAPER_BENCH_DATA_ROOT"
```

The data mirror contains 125 task-input directories, a file inventory, and
SHA-256 checksums. It deliberately excludes organization secrets, API keys, and
scratch work. Verify an individual card before running it:

```bash
python3 paperbench.py verify-data --data-root "$PAPER_BENCH_DATA_ROOT" \
  --card astro/1903.02557_dash_supernova_class
```

Historical baseline source code and reports are in Git, while its generated
outputs are an optional, separate ModelScope download. They are not needed for
running or evaluating a new submission:

```bash
export MODELSCOPE_BASELINE_ARTIFACTS_REVISION=<approved-release-tag-or-commit>
python3 paperbench.py fetch-baselines --output /mnt/d/paper-bench-baseline-artifacts
```

The archive preserves the `baselines/<domain>/<card_id>/...` layout and includes
`checksums.sha256` for maintainers auditing prior work.

Create a member submission workspace, then run the command supplied by that
submission. Task implementations have different scientific dependencies, but
every command receives a stable data environment:

```bash
python3 paperbench.py init-submission astro/1903.02557_dash_supernova_class
python3 paperbench.py run astro/1903.02557_dash_supernova_class \
  --submission submissions/astro/1903.02557_dash_supernova_class \
  --data-root "$PAPER_BENCH_DATA_ROOT" --command 'python run.py'
```

The run command receives `PAPER_BENCH_CARD_DIR`, `PAPER_BENCH_DATA_DIR`, and
`PAPER_BENCH_SUBMISSION_DIR`. Use those variables rather than a local drive
letter. See `INTERNAL_RUNBOOK.md` for the full workflow and checksum validation.

## Maintainer LLM Evaluation

Running a member solution and judging it are separate stages. Semantic scoring
against the paper truth requires the organization LLM judge and must remain in
maintainer-controlled infrastructure.

```bash
cp .env.example .env
# Set JUDGE_API_URL, JUDGE_API_KEY, and JUDGE_MODEL in .env.
set -a; . ./.env; set +a

python3 paperbench.py evaluate astro/1903.02557_dash_supernova_class \
  --submission submissions/astro/1903.02557_dash_supernova_class
```

The canonical judge accepts an OpenAI-compatible chat-completions endpoint.
Never commit the API key. The maintainer CLI writes results only inside the
ignored submission workspace; it does not overwrite benchmark baselines or
centralized historical reports.

## Participant Release

Do not grant participants access to this repository or its Git history. Generate
a new participant repository after the ModelScope dataset has been tagged or
pinned to an immutable commit:

```bash
export MODELSCOPE_DATASET_REVISION=<approved-release-tag-or-commit>
python3 paperbench.py release \
  --output ../paper-bench-participant \
  --dataset-revision "$MODELSCOPE_DATASET_REVISION" \
  --init-git
```

The generated directory has a fresh Git repository but no commit. Review it,
commit only that directory, and publish it to the participant GitHub repository.
It contains 125 minimal machine-readable cards with a task ID, paper reference,
frozen ModelScope location, and submission contract. It excludes private truth
anchors, rubrics, calibration notes, task prose, baseline submissions, evaluator
code, and evaluation results. The participant kit downloads the complete data
mirror before work begins and submits evidence for the private judge. See
`RELEASE.md`.
