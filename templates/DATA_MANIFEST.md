# Data Manifest: <domain>/<card_id>

## Release

- Dataset name: <name>
- Immutable URL or DOI: <url-or-doi>
- Version or release date: <version>
- License: <license>
- Redistribution status: <redistributable | external-download | restricted-access>

## Integrity

- Download archive SHA-256: `<sha256>`
- Extracted checksum file: `<relative/path/to/checksums.sha256>`
- Expected extracted size: <size>
- Required free disk: <size>

## Local Layout

After extraction, this directory is the data root passed to `paperbench.py`:

```text
data/
  <required-file-or-directory>
```

## Retrieval

```bash
# Put an idempotent download and extraction command here.
```

## Execution

- Environment or dependency lock: `<path or exact package versions>`
- Command from `agent_solution/`:

```bash
# Use PAPER_BENCH_DATA_DIR rather than an absolute local path.
<command>
```

## Access Notes

Describe registration, citation, or restricted-access steps. Do not place a
credential, signed URL, or local machine path in this file.
