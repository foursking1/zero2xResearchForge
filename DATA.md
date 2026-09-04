# Data Handling

paper-bench keeps large and externally sourced artifacts outside Git. Git tracks
task definitions, data metadata, code, and small evidence files only. Raw datasets,
checkpoints, embeddings, and generated arrays belong in a data repository or object
store, not in a Git commit.

## Organization Distribution

Keep this maintainer repository restricted. Organization participants receive the
separately generated Participant Kit in its own private GitHub repository and
download the separate private ModelScope mirror. They need permission to both
participant-facing services. The complete mirror is approximately 73.6 GB and
contains all 125 frozen task-input trees. Maintainer setup and LLM judging are
documented in `INTERNAL_RUNBOOK.md`.

## Local Data Layout

Use one immutable local data root:

```text
<data-root>/
  astro/
    1903.02557_dash_supernova_class/
  cs/
    2607.18127_cloudens/
  biomed/
    2604.04518v1/
```

The following command creates an ignored link at
`tasks/<domain>/<card_id>/data`. Existing submission code that uses a relative
`data/` path continues to work while the source data stays in its local location.

```bash
export PAPER_BENCH_DATA_ROOT=/mnt/d/paper-bench-data
python3 paperbench.py link-data cs/2607.18127_cloudens
python3 paperbench.py run cs/2607.18127_cloudens --command 'python run.py'
```

Use `--data-dir /absolute/path/to/one/card` when the data is not organized under
the standard root. `--dry-run` previews changes. The linker refuses to overwrite a
real `data/` directory; `--replace` can replace only an existing symlink.

Every command started through `paperbench.py run` receives
`PAPER_BENCH_DATA_DIR`. New task implementations should use that variable rather
than a hard-coded drive letter.

## What Stays Out Of Git

| Path or type | Reason |
|---|---|
| `tasks/*/*/data/` | frozen per-card inputs |
| checkpoints, tensors, and arrays (`*.pt`, `*.ckpt`, `*.npy`, etc.) | regenerable or externally stored artifacts |
| upstream source corpora and download caches | not benchmark output |
| `work/` and local environments | scratch output and machine-local dependencies |

All of these exclusions are declared in `.gitignore`.

## Participant Data Contract

The participant release references the private ModelScope mirror rather than
copying task-local manifests from this maintainer repository. Before publishing a
participant kit, the maintainer must select an immutable ModelScope tag or commit
and generate the kit with that value. The dataset release record must provide:

1. immutable release URL or DOI;
2. license and redistribution terms;
3. archive SHA-256 and extracted-file checksums;
4. expected `<data-root>/<domain>/<card_id>/` layout;
5. download and checksum-verification command plus disk requirements;
6. access policy for organization members.

The generated participant kit carries the repository, revision, relative path,
and checksum inventory in each `task.json`; it intentionally has no benchmark
answer, score target, evaluator, or task-local source path.

## ModelScope Data Mirror

The complete frozen task-input mirror is distributed separately from Git at
[`foursking1/zero2xResearchForge`](https://modelscope.cn/datasets/foursking1/zero2xResearchForge).
It is laid out as `<data-root>/<domain>/<card_id>/...`, so a download can be used
directly as `PAPER_BENCH_DATA_ROOT`. The mirror contains 125 task input trees,
`data_inventory.csv`, and `checksums.sha256`; it excludes baselines,
private anchors, scoring rubrics, calibration material, reference results, and
scratch directories.

Participant Kit users download the complete mirror through
`participantbench.py`; it detects the installed ModelScope CLI syntax, so the
same instructions work with currently supported and older organization
environments:

```bash
python3 -m pip install -U modelscope
modelscope login --token <member-token>
python3 participantbench.py fetch-data --output /mnt/d/paper-bench-data
export PAPER_BENCH_DATA_ROOT=/mnt/d/paper-bench-data
python3 participantbench.py verify-data --data-root "$PAPER_BENCH_DATA_ROOT" \
  --card cs/2607.18127_cloudens
```

Download into an empty directory; pass `--resume` only when continuing an
interrupted download. Verify the complete payload after download:

```bash
(cd /mnt/d/paper-bench-data && sha256sum -c checksums.sha256)
```

The root dataset repository declares its license as `other`: the mirrored inputs
come from multiple upstream sources with different redistribution terms. Keep the
per-task source metadata and comply with the original provider's license and
access conditions.

Maintainers can rebuild the complete mirror from an authorized frozen data root
without copying all data locally. The staging command creates links only, validates
the frozen move logs, and redacts local paths from uploaded metadata:

```bash
python3 tools/prepare_modelscope_full_data.py \
  --frozen-root /mnt/f/dataset \
  --output .paperbench/modelscope-full --stage
MODELSCOPE_API_TIMEOUT=300 MODELSCOPE_API_CONNECT_TIMEOUT=120 \
MODELSCOPE_API_TOKEN=... python3 tools/upload_modelscope_full_data.py \
  --payload .paperbench/modelscope-full/payload \
  --repo foursking1/zero2xResearchForge
```

The uploader commits and verifies small batches so it can resume cleanly after a
network timeout. The expanded timeouts accommodate ModelScope's slower commit
path for data repositories. It forces every frozen input through Git LFS, even
small `.dat`, `.csv`, and text-like data files, so line endings cannot change.
Do not put the token in a command history, source file, or Git.

The older allow-listed phase-one tool remains useful for a license-screened subset:

```bash
python3 tools/prepare_modelscope_dataset.py
```

The generated `.paperbench/data-release/` directory contains a catalog and
SHA-256 list for formal task inputs only. It excludes `baselines/` and virtual
environments. Staging payload files requires an explicit allow-list and accepts only
cards whose local metadata contains CC-BY or CC0 evidence and whose `data/`
directory includes actual input files. License evidence is still subject to manual
review before a public upload.

The catalog's `availability` field records whether a card has only local payload
files, also references external local storage, or contains metadata only. Symbolic
links and `DATA_LOCATION.md` records are deliberately excluded from the mirror. A
selected card's source/license records are copied with local paths redacted, so an
upload never exposes a local drive reference.

After reviewing the selected cards' upstream licenses, stage and verify a mirror:

```bash
python3 tools/prepare_modelscope_dataset.py \
  --output .paperbench/modelscope-phase-1 \
  --stage --cards \
  astro/2508.14107_suryabench_flare \
  biomed/2205.13760_tranception_proteingym \
  biomed/2508.04441_mitotic_benchmark \
  materials/2511.22885_mech_props_mlip
(cd .paperbench/modelscope-phase-1/payload && sha256sum -c checksums.sha256)
```

Set `MODELSCOPE_DATASET_REPO` to its `namespace/name` and put the access token in
the ignored `.env`. Upload only a verified `payload/` directory:

```bash
python3 -m pip install -U modelscope
set -a; . ./.env; set +a
modelscope upload "$MODELSCOPE_DATASET_REPO" \
  .paperbench/modelscope-phase-1/payload --repo-type dataset
```

Do not put credentials, signed URLs, or local absolute paths in a manifest. The
public release needs this metadata and checksums even when original data requires
restricted access.

## Current Portability Gap

Some legacy cards retain references to external drives such as `F:/dataset` or
`E:/scisolvebench-data`. For organization members, the ModelScope mirror and
`PAPER_BENCH_DATA_DIR` are the portable replacements. New submission code must
use the environment variable rather than copy historical paths. The private judge
falls back to validating machine-readable evidence such as `metrics.json`, a
report, or an evidence table against the private anchors where execution itself is
not part of the score.

Mark these cards as evidence-only in a future public manifest until portable data
and a run command are available. Do not solve this by adding local data, links, or
drive paths to Git or to a public data mirror.
