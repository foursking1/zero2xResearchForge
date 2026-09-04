# Solution — 2504.04211 PTA normalizing flows

**Verdict: partially_supported** (on the frozen 10-pulsar subset).

## Key numbers
- **Data:** 10 NG15 wideband pulsars, **4944 active ToAs** (matches paper Table V; the
  `C`-prefixed `.tim` rows are cut ToAs — the task's "+1/psr v2.1.0" note does not
  materialise on these frozen files).
- **Posterior (Hellinger, 2-dim SGWB marginal, reweighted):** PowerLaw 0.518,
  SMBHB 0.324, DW 0.989 → **mean 0.611** (paper 0.2611, full-22-dim).  DW is an IS
  collapse (neff=1) of the under-trained NF; its direct Hellinger is 0.482.
- **Model ranking:** MCMC and NF(IS) both give **PowerLaw > SMBHB > DW** (consistent).
  Pairwise |Δln BF| = 1.0 / 6.7 / 7.7 (SMBHB-PL / DW-PL / DW-SMBHB).
- **Evidence:** logZ MCMC (HME) 69005.6 / 68999.0 / 68993.1; logZ NF (IS)
  68975.4 / 68969.9 / 68956.3.  Learned-HME NF evidence unusable (neff≈1–2) at this scale.
- **Speed:** NF ≈ 4.8–5.5 min/model vs MCMC ≈ 11.4–13.4 min/model ⇒ **~2.3× faster**
  (direction correct; paper's 20 h-vs-10 d ratio not comparable on this reduced MCMC).

## How to reproduce
```
cd code
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" run_pta.py --n_train 15000 --n_epochs 40 --n_eval 8000 --cache code/cache_smoke --skip_mcmc --models PowerLaw,SMBHB,DW   # main run
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" pta_postprocess.py                                                                      # figures + IS-BF table
```
Outputs: `results/{metrics.json, evidence_table.csv, figure.svg, figure_logz.svg}`.

## Deviations from paper
- NF trained at 15000 sims × 40 epochs vs paper 2×10^5 × 50 (~40× fewer) — compute limit.
- MCMC reference is emcee + truncated HME, not nested sampling.
- Hellinger on 2-dim SGWB marginal vs paper's full 22-dim.
- 10 pulsars vs 68; frozen data are v2.1.0 (ToA difference reported as a data fact).
- NF evidence reported with IS estimator (learned-HME collapses under the reduced budget).
