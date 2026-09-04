# DASH (arXiv:1903.02557) — Reproduction Report

## 1. Goal
Verify, on the frozen official data, the paper's claim that the DASH CNN
classifies real OzDES supernova spectra at ~93% broad-class agreement with ATel
classifications and does so autonomously in <20 s.

## 2. Frozen data used (unchanged, SHA-256 per MANIFEST.tsv)
- `OzDES_data/` — 69 real OzDES/DES spectra (`*.dat`, 3-column wave/flux/err),
  run 24–28, matched to `all_atels.txt` (67 unique objects; DES16C3bq and
  DES16E1dcx each have 2 epochs).
- `models_v06.zip` — official DASH v06 model (TF1 checkpoints). Extracted into
  the `astrodash` package directory (`astrodash/models_v06/`); the frozen zip is
  not modified.
- Redshifts taken from `all_atels.txt` (`knownZ=True`).

Data facts (from `dash_data.py`): 69 spectra, 69 matched ATel rows, 67 unique
objects.  ATel broad-label distribution: Ia 47, Ia? 9, II 9, II? 2, Ibc 1, Ibc? 1.
Redshifts 0.033–0.57, mean 0.283.

## 3. Environment
- Python 3.13.14 (`envs/default` venv), tensorflow-cpu 2.21.0 (TF1-compat graph
  mode via `tensorflow.compat.v1`), astrodash 1.0.22.
- Two runtime compatibility shims were monkey-patched into the installed
  astrodash (package files untouched) because numpy 2.x removed behaviours the
  2019 code relied on: (a) `get_templates` ragged object-array construction;
  (b) `snInfos != []` array comparison. These shims do not change the model.

## 4. Method
- `astrodash.Classify(filenames, redshifts, knownZ=True, smooth=6)` on all 69
  spectra in one batch (official v06 `zeroZ` model).
- Paper broad-class mapping (Sec.5.2): Ia = {Ia-norm, Ia-91T, Ia-91bg, Ia-csm,
  Ia-02cx, Ia-pec}; II = {IIP, IIL, IIn}; Ibc = {Ib-norm, Ibn, IIb, Ib-pec,
  Ic-norm, Ic-broad, Ic-pec}.  ATel labels with `?` map to the uncertain member
  of the broad class.  Match = predicted broad == ATel broad.  A DASH top-1 of
  `Ic-broad` is, per the paper, host contamination and is reported separately,
  NOT counted as a match.

## 5. Results
| | frozen subset (v06) | paper (Table 1) |
|---|---|---|
| overall | 56/64 = 0.875 | 197/212 = 0.929 |
| Ia | 49/54 = 0.907 | 127/129 = 0.984 |
| II | 6/8 = 0.750 | 25/28 = 0.893 |
| Ibc | 1/2 = 0.500 | 1/1 = 1.0 |
| wall time | 3.59 s (69 spec) | <20 s / 212 |

5 predictions are top-1 `Ic-broad` (excluded per paper convention; 3 of the
label-II objects and 2 label-Ia objects).  8 mismatches remain, dominated by
label-Ia spectra predicted as Ibc subtypes (Ib-norm/Ic-norm) and label-II
spectra predicted as Ia.  Spot-check vs paper Table 2: DES16C3bq -> Ia-norm
(MATCH); DES16E2aoh -> Ia-91bg (broad-Ia MATCH).

## 6. Conclusion
**supported** on the frozen subset: overall 0.875 >= 0.80 and Ia 0.907 >= 0.90
(rubric thresholds), and the full 69-spectrum autonomous classification finished
in 3.59 s (model setup 1.55 s + forward pass 2.03 s), consistent with the
paper's <20 s / 212 claim.

## 7. Boundaries / caveats
- Frozen subset is 69 spectra (2015–2017 runs 24–28) vs the paper's 212; the
  subset composition (Ia-heavy) raises sampling noise, especially for II (n=8)
  and Ibc (n=2).
- The official v06 model differs from the 2019 paper model version; subtype-level
  and even some broad-class predictions differ (notably several SNIa predicted
  as Ibc subtypes).
- Per-object Table 2 agreement is high for the two rubric spot-check objects;
  a full 69-object Table-2 reproduction was not possible because the paper's
  Table 2 list was not provided in the frozen packet.
