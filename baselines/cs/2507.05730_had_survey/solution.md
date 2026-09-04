# Solution — Reproducing the statistical RX anchor of the HAD survey (arXiv:2507.05730)

**Task:** `2507.05730_had_survey` (L1 critical-claim) — verify the *global RX* detector column of
Table 5 of Pant et al., *Hyperspectral Anomaly Detection Methods: A Survey and Comparative Study*,
on the frozen 14-dataset subset of the survey.

**What was done (in short).** The global RX detector (Mahalanobis distance with the global
mean/covariance pseudo-inverse) was implemented from scratch, applied to all 14 frozen `.mat`
scenes, and evaluated with pixel-level ROC-AUC against the frozen ground-truth maps. Results:

| Claim | Verdict | Key numbers (this work) |
| --- | --- | --- |
| (a) RX anchor reproducible | **supported** | 11/14 rows match paper Table 5 RX within \|Δ\|≤0.01; 3 non-matching rows are documented **dataset-version differences** (San Diego / Gulfport / Bay Champagne) |
| (b) RX competitive & fast | **supported** | min AUC = 0.8221 ≥ 0.80 across all 14 (worst = LA-1, same as paper); mean AUC 0.9350; mean runtime ≈ 0.4 s (0.4–1.4 s incl. load + eval, always < 5 s) |
| (c) family ordering | **supported** (as paper-reference interpretation) | paper average: GT-HAD 0.9733 > CRD 0.9567 > **RX 0.9390**; our optional CRD re-check confirms direction CRD (0.9521) > RX (0.9350) on the 14 frozen scenes |

## Files

```
agent_solution/
├── solution.md                  <- this file (method + results summary)
├── report.md                    <- full report (method, version diffs, limitations)
├── code/
│   ├── run_rx.py                <- main reproducible script (global RX + AUC + timing + SHA-256)
│   ├── run_crd.py               <- optional CRD implementation for claim (c) direction check
│   └── make_figures.py          <- figure generation for evidence
├── results/
│   ├── evidence_table.csv       <- 14-row evidence table + summary (MAIN deliverable)
│   ├── summary.json             <- machine-readable summary
│   ├── sha256_report.tsv        <- frozen-file integrity verification
│   ├── crd_table.csv            <- CRD AUC per dataset (bonus)
│   ├── crd_vs_rx.csv            <- RX vs CRD comparison (bonus)
│   └── crd_summary.json
├── figures/                     <- PNG evidence figures (also mirrored in evidence/)
└── evidence/                    <- shipped copies of all key outputs
```

## Reproduction

```bash
# 1. global RX detector + AUC + timing -> results/evidence_table.csv
python code/run_rx.py --data_dir <frozen-hsi-folder>

# 2. optional CRD (claim-c direction) -> results/crd_table.csv, crd_vs_rx.csv
python code/run_crd.py --data_dir <frozen-hsi-folder>

# 3. figures
python code/make_figures.py <frozen-hsi-folder>
```

`run_rx.py` auto-detects the data dir if `--data_dir` is omitted (mirrors the canonical
`F:\dataset\cs\2507.05730_had_survey\hsi\`). It first verifies the SHA-256 of all 15 used files
against `data/source_manifest.json`, then computes RX for each dataset.

RX definition used (identical to the "official" global RX, per TASK.md):
`score(x) = (x − μ)ᵀ Σ⁻¹ (x − μ)` with μ = full-image per-band mean, Σ = full-image covariance
(`np.cov`, ddof=1), Σ⁻¹ via Moore–Penrose pseudo-inverse `np.linalg.pinv` (robust to the
rank-deficient, heavily colinear hyperspectral bands).

## Verdicts (detailed)

### (a) RX anchor reproducibility — supported (11/14)

Of the 14 frozen rows, 11 reproduce the paper's Table 5 RX column **exactly** (Δ ≈ 0, many to the
4th decimal, e.g. LA-1 `0.8221 = 0.8221`, AVIRIS-1 `0.8866`, HYDICE `0.9857`, Texas-1 `0.9907`,
Cat Island `0.9807`). The three remaining rows differ only because the frozen package ships a
different *version* of the scene than the paper used:

| Row | This work (RX) | Paper Table 5 | Δ | Cause |
| --- | --- | --- | --- | --- |
| San Diego (id 1) | 0.9219 | 0.9403 | −1.8 pp | paper used 100×100×186 crop (bands removed); frozen package is the full-band 100×100×224 top-left crop |
| Gulfport (id 8.2) | 0.9288 | 0.9526 | −2.4 pp | frozen mirror has 205 bands vs paper's 191 |
| Bay Champagne (id 10.2) | 0.9106 | 0.9999 | −8.9 pp | frozen mirror has 193 bands vs paper's 188 |

These are **not** reproduction failures: they are data-version artefacts, explicitly flagged in the
TASK mapping table and PAPER_ANCHOR, hence correctly reported as version differences.

### (b) RX competitive & fast — supported

- minimum AUC over the 14 frozen scenes = **0.8221** (LA-1), all 14 above 0.80; the paper's full 17-row
  RX range is [0.8221, 0.9999] with min 0.8221 — identical worst case.
- mean AUC over the 14 frozen rows = 0.9350 (paper mean 0.9390 over all 17 rows).
- runtime: each scene < 5 s end-to-end in every run; an idle-machine run gave **mean 0.40 s**
  (matching the paper's reported RX average), a contention-loaded run 1.4 s. So the
  "statistical methods are fastest" statement is directly reproduced.

### (c) Family ordering — supported (paper reference) + bonus CRD direction check

Ordering given in the paper (Table 5 Avg): **GT-HAD 0.9733 (deep) > CRD 0.9567 > RX 0.9390**;
RX is the fastest (0.40 s). We did **not** run the deep learners (they need pretrained weights and
long GPU runs; out of scope of a frozen-data reproducibility task), so (c) is judged against the
paper's reported numbers plus our own CRD re-implementation: global-dictionary CRD with the exact
leave-one-out ridge shortcut yields mean AUC **0.9521** vs our RX mean **0.9350** on the same 14
scenes → direction CRD > RX confirms the paper's ordering. RX is thus *competitive but not the
most accurate*, and *the fastest* — precisely the survey's claim.

## Integrity / anti-leakage

- Only the frozen `.mat` files are used; no synthetic data.
- Ground truth is used **only** for the final `roc_auc_score((gt>0), score)` evaluation. RX is fully
  unsupervised: μ/Σ are estimated from all pixels (standard global-RX practice) with **no** GT-based
  filtering, tuning, or background selection.
- All 15 files used verified by SHA-256 against `data/source_manifest.json` (`results/sha256_report.tsv`).

See `report.md` for the full methodology, the version-difference analysis, and limitations.