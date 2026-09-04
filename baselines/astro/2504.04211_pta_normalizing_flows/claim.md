# Claim verification: PTA normalizing-flow acceleration (arXiv:2504.04211)

## Falsifiable scientific claim (one sentence)

The normalizing-flow (NF) framework reproduces the NANOGrav 15-yr Bayesian
inference and model comparison on a 10-pulsar subset — reweighted NF posteriors
align with MCMC at mean Hellinger distance 0.2611 (paper Table I, typical ≲0.3),
NF Bayes factors agree with the MCMC reference within uncertainty (paper Table
III), and each model finishes in ~20 h vs ~10 d for MCMC.

## Failure conditions

1. Reweighted NF-vs-MCMC Hellinger mean is not ≤0.45 (rubric full-score band)
   with per-model values not mostly ≤0.5.
2. NF and MCMC Bayes-factor rankings disagree, or the magnitudes differ by more
   than the rubric tolerance (majority of pairs |Δln BF| > 1).
3. NF is not faster than MCMC per model (efficiency claim fails even in
   direction).

## Result

Data: 10 NG15 wideband pulsars, **4944 active ToAs** (matches paper Table V; the
`C`-prefixed `.tim` rows are cut ToAs, so the task's "+1/psr v2.1.0" note does not
materialise on these frozen files — reported as a data fact).  Reference
realisation r0 drawn under a PowerLaw injection (logA_gw=-15.0, γ=5.0).

| SGWB model | Hell. direct | Hell. reweighted | logZ MCMC (HME) | logZ NF (IS) | ln BF vs PL (MCMC / NF-IS) | MCMC s | NF s |
|---|---|---|---|---|---|---|---|
| PowerLaw | 0.937 | 0.518 | 69005.56 | 68975.41 | 0 / 0 | 731.5 | 323.3 |
| SMBHB | 0.965 | 0.324 | 68999.01 | 68969.86 | -6.54 / -5.55 | 684.3 | 327.6 |
| DW | 0.482 | 0.989 | 68993.14 | 68956.29 | -12.42 / -19.12 | 805.3 | 285.2 |

- Reweighted Hellinger **mean 0.611** (paper 0.2611 on the full 22-dim space; ours
  on the 2-dim SGWB marginal).  SMBHB passes (0.324), PowerLaw marginal (0.518),
  DW fails (0.989).  The DW value is an importance-sampling collapse (neff = 1/8000)
  of the under-trained NF, not a far-from-MCMC amortised posterior (its *direct*
  Hellinger is 0.482).
- BF **ranking fully consistent**: MCMC and NF-IS both order PowerLaw > SMBHB > DW.
  Pairwise |Δln BF| = 1.0 (SMBHB/PL), 6.7 (DW/PL), 7.7 (DW/SMBHB) → only 1/3 unique
  pairs within the rubric's ≤1 band.
- Learned-harmonic-mean NF evidence is unusable at this training scale (neff≈1–2,
  logZ_NF_HME ≈ −1e5…−1e6), so NF evidence is reported with the importance-sampling
  (IS) estimator, an equivalent estimator permitted by the task.
- Efficiency: NF total ≈ 4.8–5.5 min/model vs MCMC ≈ 11.4–13.4 min/model ⇒
  **~2.3× speed-up** (direction correct; the paper's ~24×/20 h-vs-10 d ratio is not
  comparable because our MCMC is a reduced 48×1200 emcee run on 10 pulsars).

## Conclusion label

**partially_supported** — the qualitative claims hold (NF posterior can match MCMC
for 1–2 models, BF model ranking is identical, NF is faster than MCMC), but the
quantitative headline (mean reweighted Hellinger 0.26 with all models ≲0.3; NF BF
within uncertainty for most model pairs) is **not** reproduced under the compute-limited
NF training (15000 forward sims × 40 epochs vs the paper's 2×10^5 × 50, i.e. ~40× fewer).
The shortfall is dominated by NF under-training / IS collapse, so it cannot be read as a
contradiction of the paper.
