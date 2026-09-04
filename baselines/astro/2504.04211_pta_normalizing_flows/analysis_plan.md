# Analysis plan — PTA normalizing flows (arXiv:2504.04211)

## Steps
1. **Data** (`pta_data.py`): parse the 10 wideband `.tim`/`.par`; count active ToAs
   (4944, matching paper Table V), white-noise levels, RA/Dec, T_obs, Nfreq.
   Report the C-prefixed-cut-ToA data fact. Build the 22-dim Gaussian joint
   likelihood (marginalised Fourier coefficients, Woodbury).
2. **Reference realisation**: draw r0 under a PowerLaw injection (paper
   forward-simulation / amortised-inference protocol) on the real grid.
3. **MCMC** (`run_pta.py`): emcee 48x1200 (burn 300) per model; truncated-HME evidence.
4. **NF**: conditional RealNVP (22-dim, 281-dim context), trained on 15000 sims x 40
   epochs (reduced vs paper 2e5 x 50); evaluate direct + importance-reweighted posterior
   on r0; Hellinger on the 2-dim SGWB marginal; IS evidence.
5. **Compare**: BF ranking and |Δln BF| (MCMC-HME vs NF-IS); timing.
6. **Post-process** (`pta_postprocess.py`): robust figures + IS-BF consistency table.
7. **Verdict**: rubric thresholds — Hellinger mean ≤0.45 (full) / 0.45-0.6 (half) /
   >0.6 (zero); BF ranking consistency + majority pairs |Δln BF| ≤1.

## Success criteria
- `results/{metrics.json, evidence_table.csv, critical_checks.json, figure*.svg}`.
- `claim.md`, `report.md`, `solution.md`, `submission/run.sh`, `provenance/data_facts.json`.

## Notes
- Frozen data unchanged (SHA-256 per MANIFEST.tsv).
- NF training reduced by ~40x due to compute; learned-HME NF evidence collapses
  (neff≈1-2), so NF evidence is reported via the IS estimator (equivalent estimator
  allowed by the task).
- Report 10-vs-68 pulsar and v2.1.0-vs-paper data-version boundaries.
