# Analysis plan — SEP Random Hivemind (arXiv:2303.08092)

## Steps
1. **Data** (`sep_data.py`): load frozen `SEPTEBBS.json`, apply the paper's exclusion
   criteria (Tmax<100 MK, non-negative time offsets/MinDur); build the 12-feature
   matrix + label; report clean rows/SEP count (24,570/74 vs paper 18,311/64).
2. **Feature weights** (`sep_models.py`): χ² + mutual-information, normalised
   (paper Eq.1–4); RH feature sampling proportional to weights (RH v1 n=4, RH v2 n=6).
3. **Models**: CoNN (12 feat, 1 net), Committee (12 feat, 10 equal nets), RH v1/RH v2
   (subsampled-feature ensembles, 10 nets, feature-weight voting). dense 10, dropout 0.2,
   balanced BCE; base epochs 150, α=1e-3; RH epochs/LR scaled by 12/n_sel.
4. **Evaluate**: 10 random stratified 70/30 splits; Youden-J threshold on training;
   per-split confusion + TSS/HSS/precision/recall/accuracy/AUC; mean±std, med±MAD.
5. **Claims** (`run_sep.py`): RH v2 med TSS ≥ CoNN; ensemble dispersion < CoNN;
   RH v2 med HSS ≥ CoNN; RH v2 ≥ Committee & RH v1.
6. **Verdict**: relative anchors primary; absolute TSS/HSS vs paper Table 2 with
   ≤±0.05 "口径一致" tolerance and data-version caveat.

## Success criteria
- `results/{metrics,evidence_table,critical_checks,uncertainty}.json`, `figures/`.
- `claim.md`, `report.md`, `solution.md`, `submission/run.sh`, `provenance/data_facts.json`.

## Notes
- Frozen data unchanged (SHA-256 per MANIFEST.tsv); no synthetic flares/SEP.
- Reduced base epochs (150 vs 500) documented as a compute limit; relative anchors primary.
- Low precision/HSS expected from the ~0.3% positive class (paper §4/§5 operating point).
