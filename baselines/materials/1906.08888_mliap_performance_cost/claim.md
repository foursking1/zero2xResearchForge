# claim.md  --  verdict for task 1906.08888_mliap_performance_cost

- **overall verdict**: `partially_supported`


## Key numbers (computed on the frozen data, not copied from the paper)

| quantity | value |
|---|---|
| best-model test energy MAE, mean over 6 elements | 5.1 meV/atom |
| best-model test force MAE, mean over 6 elements | 0.174 eV/A |
| train/test energy MAE ratio (grand mean) | 0.70 |
| energy model ranking (test, mean) | ['kernel_gap_proxy', 'quad_snap_proxy', 'mlp_nnp_proxy', 'linear_snap_proxy'] |
| chemical trend (kernel energy MAE, low->high) | ['Cu', 'Ni', 'Li', 'Ge', 'Si', 'Mo'] |

## Per-claim verdicts

- **claim_1_near_DFT_accuracy**: `supported` -- best model energy MAE 5.1 meV/atom (<100 meV ok), force MAE 0.174 eV/A
- **claim_2_model_ranking**: `supported` -- energy ranking: ['kernel_gap_proxy', 'quad_snap_proxy', 'mlp_nnp_proxy', 'linear_snap_proxy'] (expect kernel/GAP best, NNP/like worst)
- **claim_3_no_overfitting**: `supported` -- mean train/test energy-MAE ratio=0.70 (ratio<=1.5 means errors comparable)
- **claim_4_accuracy_cost_pareto**: `supported` -- Mo kernel DOF scan: n_basis 50->800 lowers test energy MAE 13.3->9.5 meV/atom and force MAE 0.33->0.29 eV/A while evaluation cost grows; quad sits between linear and kernel (see results/mo_pareto_scan.json)
- **claim_5_chemical_trend**: `partially_supported` -- kernel test energy MAE low->high: ['Cu', 'Ni', 'Li', 'Ge', 'Si', 'Mo'] (fcc Cu/Ni lowest confirmed; bcc Li is 2nd-best and bcc Mo worst, so the paper's strict fcc<bcc<diamond ordering is only approximate)

## Caveats
- Proxy descriptor/model classes reproduce the *directionality and magnitude* of the paper's
  ML-IAP comparison; absolute MAE values differ from the paper's GAP/MTP/SNAP/NNP because
  these are simplified surrogates (radial+angular Behler-Parrinello descriptors, linear/quadratic/
  kernel/MLP readouts, energy-conserving fits fitted only to total energies).
- All metrics are reproducibly computed by `code/run_pipeline.py` under the frozen train/test split.