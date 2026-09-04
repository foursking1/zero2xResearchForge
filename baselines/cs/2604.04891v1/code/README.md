# Verification code for arXiv 2604.04891v1 (agent_solution/code)

All data is read **in place** from the frozen dataset `F:\dataset\2604.04891v1`
(no data copied). Set `PAPER_DATA_ROOT` to override the data root if needed.

## Canonical runnable scripts

| Script | What it does | Run order |
|---|---|---|
| `common.py` | shared helpers (Schatten norms, plan feasibility, data loading) | imported, no main |
| `verify_static.py` | Claim C01: recompute the 3 spectral-OT costs from the frozen couplings; independently re-solve with Hungarian (p=1) and CVXPY/SCS (p=2, ∞) on the same frozen clouds; plan-difference metrics | 1 |
| `verify_flow.py` | Claim C02: re-run the 3 MMD gradient flows (6000 steps) on the frozen clouds, compare loss curves vs frozen, compute trajectory/velocity coordination metrics, write figures | 2 |
| `robustness_flow.py` | C02 sensitivity check: shorter horizon (2000 steps) and ±10 % step sizes on the frozen clouds | 3 |
| `make_evidence.py` | Assemble `../results/evidence_table.csv` and `../results/metrics.json` from the JSON outputs | 4 |

## Requirements

```
pip install numpy scipy torch matplotlib cvxpy
```

Notes:
- `torch.set_num_threads(1)` is used in the flow scripts. On this machine the
  default multi-threaded BLAS is ~30× slower for the tiny (200×2) matrices
  (1083 ms/step vs 33 ms/step), which would make the 6000-step runs impractical.
- The frozen p=2 / p=∞ static couplings were produced by the reference CVXPY/SCS
  solve at finite tolerance; `verify_static.py` reports the marginal errors.

## Outputs

JSON reports are written to `../results/`:
- `metrics_static.json`, `metrics_flow.json`, `metrics_flow_robustness.json`
- `evidence_table.csv`, `metrics.json`
- figures `mmd_trajectories_three_recomputed.png`, `mmd_losses_three_recomputed.png`

## Scratch / temp files

Files with `*.tmp.*`, `_writetest.py`, and `*_v2.py` / `*_v3.py` are working
scratches left by the authoring process and can be ignored (the canonical
versions are the files listed above). `verify_flow_v2.py` and `make_evidence_v2.py`
are byte-identical to their canonical counterparts.
