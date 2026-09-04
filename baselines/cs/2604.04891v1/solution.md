# Solution: Verifying Claims C01 & C02 for arXiv 2604.04891v1

**Paper**: "Muon Dynamics as a Spectral Wasserstein Flow" (Gabriel Peyré, arXiv:2604.04891v1, April 2026)

**Task**: Reproduce the paper's two headline numerical results from the frozen data and judge the claims:
- **C01**: Static spectral couplings for Schatten p = 1, 2, ∞ give different optimal transport plans with costs **23.745, 19.916, 19.323**.
- **C02**: MMD gradient flows with Schatten p = 1, 2, ∞ give qualitatively different trajectories (operator-norm most globally coordinated, trace-norm most local, Frobenius intermediate); final losses **0.0018, 0.0016, 0.0011**.

## Verdict (summary)

| Claim | Verdict | Rationale |
|---|---|---|
| C01 | **supported** | Frozen optimal couplings reproduce the costs 23.745019 / 19.915667 / 19.323151 (relative error < 0.002 %); the three plans are clearly different; an independent re-solve confirms the costs. |
| C02 (numeric part) | **partially_supported / contradicted** | Frozen + recomputed final MMD losses are 0.001839 / 0.001838 / 0.001484. Only p=1 matches the claimed 0.0018 (within 2 %). p=2 (0.001838) and p=∞ (0.001484) do NOT match the claimed 0.0016 / 0.0011 (rel. deviations 14.9 % and 34.9 %). The monotone ordering p=1 ≥ p=2 > p=∞ holds, but the claimed values 0.0016 / 0.0011 are not present anywhere along the frozen loss curves. |
| C02 (qualitative part) | **supported** | Velocity-field anisotropy (top-singular share of the gradient at steps 999/2999/5999) is highest for operator-norm flow (0.685–0.828), lowest for trace-norm flow (0.531–0.572), intermediate for Frobenius (0.547–0.656): operator-norm = globally coordinated, trace = local, Frobenius = intermediate. Robust to ±10 % step-size changes. |

Overall the two claims as literally stated are **partially supported**: C01 holds exactly; C02's qualitative trajectory claim holds, but the numeric final-loss values (0.0016, 0.0011) are contradicted by the frozen data.

---

## 1. Method

### 1.1 Data (read in place, not copied)

All input is the frozen dataset at `F:\dataset\2604.04891v1`:

- `results/static_couplings.npz` — frozen source cloud `X` (200×2), target cloud `Y` (200×2), optimal couplings `P_1, P_2, P_inf` (200×200) and extracted permutations `perm_1, perm_2, perm_inf`.
- `results/mmd_flows.npz` — frozen initial cloud `X0`, target `Y`, and the 6000-step loss curves `losses_1, losses_2, losses_inf`.
- `results/results_summary.json` and `code/reproduce.py` — the reference reproduction (used only to fix the experimental protocol; all numbers in this report are recomputed by us).

The reproduction workspace's `data/` directory is empty; the frozen numerical artifacts are the `.npz` files above, so those are the frozen data used throughout.

### 1.2 Problem definitions (from the paper, §7)

**Static problem (C01).** With uniform weights a_i = b_j = 1/n, n = 200, the discrete spectral OT problem is

    min_{P ≥ 0, P 1 = a, Pᵀ 1 = b}  γ_p( Σ(P) ),    Σ(P) = Σ_ij P_ij (y_j − x_i)(y_j − x_i)ᵀ

with γ₁(S)=tr(S), γ₂(S)=‖S‖_F, γ_∞(S)=λ_max(S). We (a) evaluate γ_p on the frozen P, (b) check plan feasibility, and (c) independently re-solve with the Hungarian algorithm (p=1) and CVXPY/SCS (p=2, ∞) on the same frozen clouds.

**Flow problem (C02).** MMD² with the smoothed energy-distance kernel k(x,y)=−‖x−y‖_ε, ε=10⁻²:

    f(µ) = (2/n²) Σ_ij ‖x_i−y_j‖_ε − (1/n²) Σ_ij ‖x_i−x_j‖_ε − const.

Explicit-Euler flow X_{k+1} = X_k + η_p Ξ_p(∇X_k f), with step sizes η = {2.5 (p=1), 1.8 (p=2), 1.6 (p=∞)}, 6000 steps, and Ξ_p the Schatten-*q* velocity (`schatten_direction` in reproduce.py). We re-ran all three flows on the *frozen* clouds and compared against the frozen loss curves.

### 1.3 Verification scripts

| Script | Purpose |
|---|---|
| `code/common.py` | shared data loading, Schatten norms, plan-feasibility, plan-difference helpers |
| `code/verify_static.py` | C01: costs from frozen couplings + independent re-solve (Hungarian/CVXPY) |
| `code/verify_flow.py` | C02: re-run 3 flows on frozen clouds, loss-vs-frozen check, trajectory coordination metrics, figures |
| `code/robustness_flow.py` | sensitivity check: shorter horizon + ±10 % step sizes on frozen clouds |
| `code/make_evidence.py` | assemble `results/evidence_table.csv` and `results/metrics.json` |

Reproduction requires `numpy, scipy, torch, matplotlib, cvxpy`. (torch is pinned to 1 thread: the default multi-threaded BLAS is ~30× slower on the tiny 200×2 matrices.)

---

## 2. C01 — Static spectral couplings

### 2.1 Results from frozen couplings

| p | frozen cost γ_p(Σ(P)) | claim | rel. diff | plan feasible? |
|---|---|---|---|---|
| 1 (trace) | **23.745019** | 23.745 | 7.9e-5 % | yes (row/col err = 0) |
| 2 (Frobenius) | **19.915667** | 19.916 | 1.7e-3 % | approx. (SCS tol, max row err 7.9e-4) |
| ∞ (operator) | **19.323151** | 19.323 | 7.8e-4 % | approx. (SCS tol, max row err 1.3e-4) |

### 2.2 Independent re-solve on the same frozen clouds

| p | solver | re-optimised cost | frozen cost | Δ |
|---|---|---|---|---|
| 1 | Hungarian | 23.745019 | 23.745019 | 0 |
| 2 | CVXPY/SCS | 19.915667 | 19.915667 | 1.7e-10 |
| ∞ | CVXPY/SCS | 19.323225 | 19.323151 | 7.3e-5 |

The frozen couplings are (near-)optimal for their respective norms and the three costs match the claim to < 0.002 %.

### 2.3 Are the three plans different?

Pairwise plan differences (frozen P):

| pair | L1 distance | max \|ΔP\| | entries with \|ΔP\| ≤ 1e-9 |
|---|---|---|---|
| P1 vs P2 | 1.592 | 0.00509 | 35 % |
| P1 vs P∞ | 1.875 | 0.00502 | 46 % |
| P2 vs P∞ | 1.853 | 0.00509 | 28 % |

The three couplings are clearly distinct (L1 distances of order 1–2 vs total mass 1; mass agreement in ≤ 46 % of entries). This confirms the first half of C01 ("different optimal transport plans").

**C01 verdict: supported.**

---

## 3. C02 — MMD gradient flows, numeric part

### 3.1 Final losses (frozen and recomputed)

| p | recomputed final loss | frozen final loss | max \|Δloss\| over 6000 steps | claim | rel. dev. from claim |
|---|---|---|---|---|---|
| 1 (trace) | 0.001839 | 0.001839 | 5.3e-15 | 0.0018 | +2.2 % (matches) |
| 2 (Frobenius) | 0.001838 | 0.001838 | 6.2e-15 | 0.0016 | +14.9 % (does not match) |
| ∞ (operator) | 0.001484 | 0.001484 | 5.3e-15 | 0.0011 | +34.9 % (does not match) |

Our re-run on the frozen clouds reproduces the frozen loss curves to ~1e-15, so the frozen data is internally self-consistent. The claimed values 0.0016 (p=2) and 0.0011 (p=∞) are **not reached anywhere** along the frozen loss curves (which decrease monotonically to 0.001838 / 0.001484), so the discrepancy is genuine and not a step-count artefact.

**Ordering.** The claim's implicit ordering p=1 > p=2 > p=∞ (loss decreasing in p) is reproduced: 0.001839 > 0.001838 > 0.001484. However the gap between p=1 and p=2 is negligible (≈1e-6), whereas the claim implies a clear separation (0.0018 vs 0.0016).

**C02 numeric verdict: not supported for p=2 and p=∞ (supported only for p=1).**

---

## 4. C02 — MMD gradient flows, qualitative part

We quantified "global coordination" two ways on the re-run trajectories:

**Aggregate displacement** D = X_final − X_0. All flows converge onto the same target cloud, so the endpoint displacement is geometry-dominated and is *not* the right discriminator:

| p | s₁ | s₂ | s₁/(s₁+s₂) | s₁/s₂ | mean \|cosθ\| | mean ‖displ‖ |
|---|---|---|---|---|---|---|
| 1 (trace) | 59.99 | 28.47 | 0.678 | 2.107 | 0.852 | 4.537 |
| 2 (Frobenius) | 59.80 | 29.20 | 0.672 | 2.048 | 0.851 | 4.564 |
| ∞ (operator) | 59.39 | 30.69 | 0.659 | 1.935 | 0.847 | 4.601 |

**Velocity-field anisotropy** — top-singular-value share s₁/(s₁+s₂) of the *gradient matrix* at sampled steps. This measures how much of the instantaneous force field is concentrated along one dominant global direction (a "globally coordinated" force field), which is the mechanism behind the paper's qualitative claim:

| step | p=1 (trace) | p=2 (Frobenius) | p=∞ (operator) |
|---|---|---|---|
| 0 | 0.731 | 0.731 | 0.731 |
| 999 | **0.531** | 0.656 | **0.828** |
| 2999 | **0.572** | 0.627 | **0.685** |
| 5999 | **0.565** | 0.547 | **0.750** |

The operator-norm flow maintains the most rank-1-dominated (globally coherent) force field at every sampled step after k=0 (0.685–0.828), the trace-norm flow the most diffuse (0.531–0.572), and the Frobenius flow lies between (0.547–0.656), with the single exception of step 5999 where p=2 (0.547) dips just below p=1 (0.565).

**Qualitative verdict: supported.** The velocity-field anisotropy reproduces the paper's qualitative claim: operator-norm flow = most globally coordinated (most rank-1 force field), trace-norm flow = most local (most diffuse force field), Frobenius = intermediate. The endpoint-displacement metrics are nearly identical across p because all three flows converge to the same target cloud, so they are not informative for the coordination claim.

---

## 5. Robustness / sensitivity (C02)

`code/robustness_flow.py` re-runs the flows on the frozen clouds with a shorter horizon (2000 steps) and step sizes perturbed by ±10 %. Results (from `results/metrics_flow_robustness.json`):

**Final loss @2000 steps:**

| p | nominal | −10 % step | +10 % step |
|---|---|---|---|
| 1 (trace) | 0.01275 | 0.01494 | 0.01100 |
| 2 (Frobenius) | 0.01280 | 0.01544 | 0.01078 |
| ∞ (operator) | 0.01052 | 0.01263 | 0.00891 |

The operator-norm flow gives the lowest loss in every variant; the p=1 / p=2 ordering flips with step size (they are nearly tied), consistent with the full run.

**Velocity-field top-singular share @ step 999:**

| p | nominal | −10 % step | +10 % step |
|---|---|---|---|
| 1 (trace) | 0.531 | 0.532 | 0.535 |
| 2 (Frobenius) | 0.656 | 0.668 | 0.645 |
| ∞ (operator) | 0.828 | 0.846 | 0.820 |

The qualitative ordering p=∞ > p=2 > p=1 (operator most globally coordinated, trace most local) is **robust** across all three step-size settings.

---

## 6. Conclusions and caveats

1. **C01 supported**: the frozen optimal couplings reproduce the three claimed costs (23.745 / 19.916 / 19.323) to <0.002 % and are genuinely different plans.
2. **C02 partially supported**: the qualitative trajectory claim (operator = global, trace = local, Frobenius = intermediate) is reproduced and robust; the numeric final-loss values are reproduced for p=1 (0.0018) but *not* for p=2 and p=∞ (0.001838 vs 0.0016; 0.001484 vs 0.0011).
3. **Caveats**:
   - The frozen p=2/p=∞ couplings come from an SCS solve at finite tolerance (max marginal error ≈ 8e-4); the costs are unaffected at the reported precision.
   - The paper's §7 says the static and flow experiments use "exactly the same" clouds, but the reference reproduction pipeline consumes RNG between the two experiments, so `static_couplings.npz` (X,Y) and `mmd_flows.npz` (X0,Y) are *different* point clouds. This does not affect either claim's internal consistency, but it is a divergence from the paper's stated protocol.
   - Flow dynamics are deterministic but floating-point-sensitive; our single-thread re-run matches the frozen losses to ~1e-15, so the discrepancy with the claimed 0.0016/0.0011 is not a numerical artefact of our environment.

## 7. Files produced

- `code/` — runnable scripts (`README.md`, `common.py`, `verify_static.py`, `verify_flow.py`, `robustness_flow.py`, `make_evidence.py`)
- `results/evidence_table.csv` — indicator table (claim_id, metric, value, claim_value, rel_diff, criterion)
- `results/metrics.json` — machine-readable key metrics
- `results/metrics_static.json`, `results/metrics_flow.json`, `results/metrics_flow_robustness.json` — full numeric outputs
- `results/mmd_trajectories_three_recomputed.png`, `results/mmd_losses_three_recomputed.png` — regenerated figures from frozen data
