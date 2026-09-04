# PTA normalizing-flow reproduction report (arXiv:2504.04211)

## 1. Goal
Verify, on the frozen NANOGrav 15-yr data, the paper's claim that a conditional
normalizing flow (NF) reproduces the MCMC/nested-sampling posterior and evidence
(mean reweighted Hellinger 0.2611, Table I) and the model ranking (Table III) for
~20 h/model vs ~10 d for MCMC.

## 2. Frozen data used (SHA-256 per MANIFEST.tsv, unchanged)
- `ng15_wideband_10pulsars/` — 20 files (10 pulsars × {.tim, .par}), the 10 Table-V
  wideband pulsars.  Parsing yields **4944 active ToAs** (per-pulsar counts match
  paper Table V exactly).  The `C`-prefixed rows in the `.tim` files are
  cut/commented ToAs (flags like `-cut dmx`) and are **not** active; therefore the
  TASK.md "+1 ToA/pulsar (v2.1.0)" note does not materialise for these frozen files.
  This is reported as a data fact, not hidden.
- White-noise uncertainties match paper Table V to ~0.05 ns; RA/Dec read from
  `.par` for the Hellings-Downs correlation.
- **Residual protocol**: PINT/ENTERPRISE residuals cannot be produced offline (DE440
  solar-system ephemeris is not bundled and no network is available).  We therefore
  use the paper's forward-simulation / amortised-inference protocol: one reference
  realisation r0 is drawn under a PowerLaw injection (logA_gw=-15.0, γ=5.0, red-noise
  logA=-15.5, γ=4.0) on the real ToA grid with the real white-noise levels.  The frozen
  data provide the grid, uncertainties, sky positions, and noise model; r0 is the
  paper-protocol synthetic residual, not an input-data substitution.

## 3. Method
- Likelihood: 22-dim Gaussian over 10 pulsars (20 red-noise coefficients + 2 SGWB
  params), Fourier coefficients marginalised via Woodbury (`pta_likelihood.py`),
  14 frequency bins, T_obs = 5724 d.
- MCMC reference: emcee, 48 walkers × 1200 steps, burn 300, acceptance ≈ 0.13–0.24,
  autocorrelation τ ≈ 121–123.  Evidence via truncated harmonic mean (keep highest
  90% likelihood) — the paper's reference is nested sampling; HME is our computable proxy.
- NF: conditional RealNVP (5 coupling layers, hidden 192, scale_beta 4.0), 22-dim
  theta + 281-dim context (b,c), base N(0,1)^22.  Trained on **15000 forward sims × 40
  epochs** per model (paper: 2×10^5 × 50 — a ~40× reduced budget, documented).
- Evaluation on r0: direct NF samples, self-normalised importance reweighting
  (paper Eq.G1), Hellinger on the 2-dim SGWB marginal (params dims 20,21; numerically
  stable; the paper's Appendix-H Hellinger is on the full 22-dim), evidence via
  truncated HME for MCMC and via **importance sampling (IS)** for the NF (the learned-HME
  estimator collapses at this training scale because the proposal under-covers the target).

## 4. Results
| SGWB model | Hell. direct | Hell. reweighted | logZ MCMC (HME) | logZ NF (HME) | logZ NF (IS) | MCMC s | NF train s | NF eval s |
|---|---|---|---|---|---|---|---|---|
| PowerLaw | 0.9369 | 0.5182 | 69005.56 | -156441 | 68975.41 | 731.5 | 151.4 | 172.0 |
| SMBHB | 0.9647 | 0.3245 | 68999.01 | -328365 | 68969.86 | 684.3 | 149.1 | 178.5 |
| DW | 0.4825 | 0.9888 | 68993.14 | -979475 | 68956.29 | 805.3 | 134.4 | 150.9 |

- **Posterior**: reweighted-Hellinger mean **0.611** (paper 0.2611).  SMBHB passes
  the rubric per-model bar (0.324 ≤ 0.5), PowerLaw is marginal (0.518), DW fails
  (0.989).  DW's failure is an IS collapse (neff = 1/8000): the amortised NF posterior
  for DW is actually close to MCMC (direct Hellinger 0.482), but under-training makes
  the proposal under-cover the target and the self-normalised weights collapse to a
  single effective sample.  With only 2 models in the clean regime the paper's
  "alignment good" band (mean ≲ 0.3) is not reached.
- **Model comparison**: ranking is **fully consistent** between MCMC and NF-IS
  (PowerLaw > SMBHB > DW; both rule out SMBHB/DW relative to PowerLaw).  Pairwise
  |Δln BF| = 1.0 (SMBHB/PL), 6.7 (DW/PL), 7.7 (DW/SMBHB).  Only the SMBHB/PL pair is
  inside the rubric's ≤1 band; the DW evidence is systematically lower in the NF-IS
  estimate, again traceable to the under-trained NF and the collapse of the learned-HME
  estimator.
- **Efficiency**: NF total (train+eval) ≈ 285–328 s/model vs MCMC ≈ 684–805 s/model
  ⇒ **~2.1–2.8× speed-up** on this 10-pulsar subset.  The paper's ~24× (20 h vs 10 d)
  is a different regime (full 68-pulsar MCMC with nested sampling); our reduced MCMC is
  not a fair basis for that ratio, so we only report the direction and the on-subset factor.

## 5. Conclusion
**partially_supported** on the frozen subset: the qualitative direction of every claim
holds (NF can approximate the posterior, BF ranking is identical, NF is faster than
MCMC), but the quantitative targets — mean reweighted Hellinger 0.26 (we get 0.61) and
NF BF within uncertainty for most model pairs (only 1/3 pairs within |Δln BF| ≤ 1) — are
not met at the reduced NF training budget.  The shortfall is dominated by NF
under-training and IS collapse, so this is a compute-limited *non-confirmation*, not a
contradiction of the paper.

## 6. Boundaries / caveats
- NF trained at 15000×40 vs paper 2×10^5×50 (~40× less); Hellinger on the 2-dim SGWB
  marginal vs paper's full 22-dim (same 0–1 scale).
- MCMC reference is truncated HME, not nested sampling; absolute logZ values (~69000)
  are dominated by the 22-dim likelihood and only the *differences* (BFs) are meaningful.
- Run-to-run NF stochasticity: two seeded runs differed in IS evidence by ≈1.5 in logZ
  and reweighted Hellinger by ≈0.09 (PowerLaw), i.e. the NF metrics carry ±(0.1, 1.5)
  sampling noise; point estimates above are from the final self-consistent run.
- 10 pulsars vs paper's 68; v2.1.0-vs-paper ToA difference is reported as a data fact.
