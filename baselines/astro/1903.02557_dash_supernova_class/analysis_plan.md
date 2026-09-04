# Analysis plan — DASH (arXiv:1903.02557)

## Steps
1. **Data parsing** (`dash_data.py`): read `all_atels.txt`, glob all `*.dat`,
   match each spectrum to its ATel row by object name, normalise ATel labels to
   broad classes (Ia / II / Ibc, `?` kept as uncertain member; Ic-broad handled
   separately).  Verify counts vs MANIFEST (69 `.dat`).
2. **Environment** (`dash_run.py`): install astrodash + tensorflow-cpu in the
   `envs/default` venv; extract frozen `models_v06.zip` into the astrodash
   package dir; apply two numpy-2.x runtime compatibility shims to astrodash.
3. **Classify** (`dash_run.py`): `astrodash.Classify(filenames, redshifts,
   knownZ=True, smooth=6)` over all 69 spectra in one batch; record top-1
   subtype + softmax probability + reliability flag + wall-clock time.
4. **Match** (`dash_run.py`): compare DASH top-1 broad class to ATel broad
   class; exclude `Ic-broad` top-1 predictions per paper Sec.5.2; report overall
   and per-type rates + time.
5. **Verdict**: rubric thresholds — overall >= 0.80 AND Ia >= 0.90 => supported.

## Success criteria
- `results/metrics.json` with overall/per-type match rates + timing.
- `results/evidence_table.csv` (per-spectrum rows).
- `results/critical_checks.json` (claim pass/fail per rubric).
- `claim.md`, `report.md`, `solution.md`.

## Notes
- Frozen data must be used unchanged; no synthetic spectra.
- Model must be the official v06.
- Report environment (TF1-compat, astrodash version, numpy shims).
