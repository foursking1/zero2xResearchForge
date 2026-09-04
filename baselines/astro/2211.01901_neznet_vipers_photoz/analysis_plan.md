# Analysis plan — VIPERS photometric redshifts (arXiv:2211.01901)

## Steps
1. **Data** (`analyze_vipers.py`): parse the frozen official match tables
   `W1_PHOT-SPEC_MATCH_PDR.txt` (40,315 rows) and `W4_PHOT-SPEC_MATCH_PDR.txt`
   (27,961 rows); build the 19-column array (num, alpha, delta, selmag, zspec,
   zflg, zphot, u/g/r/i/z/Ks and errors).
2. **Baseline SED photoz quality** (paper Eq.5-8): σ = sqrt(mean(((zs-zp)/(1+zs))²)),
   bias, |bias|, outlier rate = |zs-zp| ≥ 0.15(1+zs).  Safe sample: zflg≤14 and zspec>0.
   Compute on W4 (primary) and W1 (supplement).
3. **Nearest-neighbour analysis**: W4 safe sample, scipy cKDTree on unit-sphere
   RA/Dec; angular distance via haversine (paper Eq.3); physical pair |Δz| ≤ 0.08(1+zs);
   physical-pair fraction vs angular-separation bins.
4. **Compare** with the paper's σ≈0.08 / outlier≈3% and Fig-1 dilution trend.
5. **Verdict**: supported if baseline quality is same order as paper and the
   physical-pair fraction declines monotonically with angular separation.

## Success criteria
- `results/{metrics.json, evidence_table.csv}` (baseline + nearest-neighbour).
- `claim.md`, `report.md`, `solution.md`, `submission/run.sh`, `provenance/data_facts.json`.

## Notes
- Frozen data unchanged (official NezNet GitHub match tables, MIT license).
- Model-improvement numbers (σ→0.04, outlier→0.8%, ~75% retained) require the NezNet
  weights which are not in the frozen packet — cannot be recomputed from data alone.
- Report W4 full-table vs paper random ~2×10^4-subset difference as a boundary.
