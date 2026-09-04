"""
CPGD and CAPGD attacks under the frozen URL constraints.

Attack space: z-score standardized features; L2 perturbation with eps=0.5 in
that space (same convention as the MOEVA/CAA framework the paper builds on).
Constraints are enforced by mapping back to the RAW feature space
(repair operator R_Omega + box/type constraints from url_features.csv).

objective (Eq. (4) of the paper)::
    L'(x) = l(h(x), y) - sum_w penalty(x, w)

CPGD (Eq. (3)): single start = original sample, predefined decaying step
schedule  eta(k) = eps * 10^-(1+floor(k/floor(K/M))), M=7, and R_Omega
before evaluation of the loss.
CAPGD (Algorithm 1): adaptive step (eta0 = 2*eps, halving w/ rho=0.75),
checkpoint set W from p0=0, p1=0.22, p_{j+1}=p_j+max(p_j-p_{j-1}-0.03,0.06),
momentum alpha=0.75, repair operator R_Omega, double initialization
(original + random sample of the L2 ball).
"""

from __future__ import annotations

import numpy as np
import torch

from constraints import URLConstraintSet, inv_standard_scaler, standard_scaler


def binary_ce_loss(model, z, y):
    """Binary cross-entropy loss from logits (float32 model)."""
    logits = model(z.float())
    return torch.nn.functional.binary_cross_entropy_with_logits(logits, y.float())


class ConstrainedAttack:
    """Shared machinery: loss, projection onto the L2 ball, repair wrapper."""

    def __init__(self, model, fmin, frange, cset: URLConstraintSet, eps=0.5,
                 device="cpu", normalize_grad=True):
        self.model = model.to(device)
        self.fmin = fmin.double().to(device)
        self.frange = frange.double().to(device)
        self.cset = cset
        self.eps = eps
        self.device = device
        self.normalize_grad = normalize_grad
        # move constraint tensors to the right device/precision
        self.cset.d_min = self.cset.d_min.to(device)
        self.cset.d_max = self.cset.d_max.to(device)
        self.cset.delta = self.cset.delta.to(device)
        self.cset.is_int = self.cset.is_int.to(device)
        self.cset.lin_c = self.cset.lin_c.to(device)
        self.cset.lin_c0 = self.cset.lin_c0.to(device)
        self.cset.lin_norm2 = self.cset.lin_norm2.to(device)
        self.cset.imp_a = self.cset.imp_a.to(device)
        self.cset.imp_b = self.cset.imp_b.to(device)

    # ------------------------------------------------------------------ #
    def _raw(self, z):
        return z * self.frange + self.fmin

    def _std(self, x):
        return (x - self.fmin) / self.frange

    def loss(self, z, y, kind="ce", penalized=True):
        """Maximized attacker objective, tensor [B].

        ``kind="ce"``:     L'(x) = CE(h(x), y)  (paper Eq. 4).
        ``kind="margin"``: L'(x) = -margin(h(x), y) with margin = logit of
                           the true class (binary). Unlike CE this does not
                           saturate for very confident samples; it is the
                           standard objective of gradient attacks (cf.
                           AutoAttack margin losses).
        ``penalized``:     when True the constraint-penalty terms of Eq. (4)
                           are subtracted (CPGD baseline, whose design relies
                           on the penalty to steer toward feasibility). The
                           CAPGD repair operator R_Omega enforces feasibility
                           by projection, and the penalty *gradient* (which is
                           non-zero wherever a feature rests on its boundary,
                           e.g. count features at their min = 0) would
                           otherwise fight the classification gradient -- so
                           CAPGD is run with ``penalized=False``.
        """
        if not torch.is_tensor(y):
            y = torch.as_tensor(y, dtype=torch.float64, device=z.device)
        if kind == "ce":
            model_loss = binary_ce_loss(self.model, z, y).double()
        elif kind == "margin":
            logits = self.model(z.float()).double()
            model_loss = -((2.0 * y - 1.0) * logits)  # -margin (binary)
        else:
            raise ValueError(kind)
        if penalized:
            pen = self.cset.total_penalty(self._raw(z))
            return model_loss - pen
        return model_loss

    def grad(self, z, y, kind="ce", penalized=True):
        z = z.clone().requires_grad_(True)
        L = self.loss(z, y, kind=kind, penalized=penalized)
        g = torch.autograd.grad(L.sum(), z)[0]
        return g

    def project_ball(self, z, z0):
        """P_S: L2 projection onto {z : ||z - z0||_2 <= eps}."""
        delta = z - z0
        n2 = delta.norm(dim=-1)
        scale = torch.clamp(self.eps / torch.clamp(n2, min=1e-15), max=1.0)
        return z0 + delta * scale.unsqueeze(-1)

    def repair(self, z, round_int=False):
        """R_Omega: map to raw, repair, map back to the standardized space.

        ``round_int=False`` keeps integer features continuous during the
        gradient iterations (rounding would erase small moves); the final
        output uses ``round_int=True`` so reported examples are valid.
        """
        raw = self._raw(z)
        raw_r = self.cset.repair(raw, n_passes=3, round_int=round_int)
        return self._std(raw_r)

    # ------------------------------------------------------------------ #
    def success_mask(self, z, z0, y_pred_orig, y):
        """is_adv: feasible AND classification differs AND within eps."""
        raw = self._raw(z)
        feasible = self.cset.is_feasible(raw)
        logits = self.model(z.float()).detach()
        pred = (logits >= 0).to(torch.int64)
        misclassified = pred != y
        within_eps = (z - z0).norm(dim=-1) <= self.eps + 1e-9
        return feasible & misclassified & within_eps


def _step_schedule_cpgd(n_iter: int, eps: float, M: int = 7):
    """eta(k) = eps * 10^-(1 + floor(k/floor(K/M))), K = n_iter - 1."""
    K = max(n_iter - 1, 1)
    denom = max(K // M, 1)
    return np.array([eps * 10.0 ** (-(1 + k // denom)) for k in range(n_iter)])


def capgd_checkpoints(n_iter: int):
    """W from p0=0, p1=0.22, p_{j+1}=p_j+max(p_j-p_{j-1}-0.03, 0.06)."""
    ps = [0.0, 0.22]
    while True:
        nxt = ps[-1] + max(ps[-1] - ps[-2] - 0.03, 0.06)
        if nxt >= 1.0:
            break
        ps.append(nxt)
    W = set()
    for p in ps[1:]:
        w = int(np.ceil(p * n_iter))
        if w <= n_iter:
            W.add(w)
    return W


def run_cpgd(ctx: ConstrainedAttack, z0, y, n_iter=10, seed=0, kind="ce", penalized=True):
    """CPGD: single start = original, predefined decaying schedule
    (eta(k)=eps*10^-(1+floor(k/floor(K/M))), M=7), R_Omega at each step.
    Objective: paper Eq. (4), CE - penalties (faithful baseline)."""
    z = z0.clone()
    eta = _step_schedule_cpgd(n_iter, ctx.eps)
    for k in range(n_iter):
        g = ctx.grad(z, y, kind=kind, penalized=penalized)
        if ctx.normalize_grad:
            g = g / torch.clamp(g.norm(dim=-1, keepdim=True), min=1e-10)
        z = ctx.project_ball(z + eta[k] * g, z0)
        z = ctx.repair(z, round_int=False)
    return z


def run_capgd(ctx: ConstrainedAttack, z0, y, n_iter=10, seed=0, kind="margin", penalized=None):
    if penalized is None:
        penalized = (kind != "margin")
    """CAPGD (Algorithm 1): adaptive step, momentum, repair, double start."""
    B = z0.shape[0]
    device = z0.device
    best_z = z0.clone()
    best_L = -torch.full((B,), float("inf"), dtype=torch.float64, device=device)

    pen = penalized
    for start in ["orig", "rand"]:
        rng = torch.Generator(device="cpu").manual_seed(seed + (0 if start == "orig" else 1000))
        if start == "orig":
            x_before = z0.clone()
        else:
            # uniform sample of the L2 ball of radius eps centered on z0
            xi = torch.randn(B, z0.shape[1], generator=rng, dtype=torch.float64, device=device)
            xi = xi / torch.clamp(xi.norm(dim=-1, keepdim=True), min=1e-15)
            r = (torch.rand(B, 1, generator=rng, dtype=torch.float64, device=device)
                 .pow(1.0 / xi.shape[1]))
            x_before = z0 + (r * xi * ctx.eps)

        z_prev = x_before
        L0 = ctx.loss(z_prev, y, kind=kind, penalized=pen)  # L'(x(0))
        # x(1) = P_S(x(0) + eta0 * grad(L'(x(0))))
        g0 = ctx.grad(z_prev, y, kind=kind, penalized=pen)
        if ctx.normalize_grad:
            g0 = g0 / torch.clamp(g0.norm(dim=-1, keepdim=True), min=1e-10)
        eta = torch.full((B,), 2.0 * ctx.eps, dtype=torch.float64, device=device)
        z = ctx.project_ball(x_before + eta.unsqueeze(-1) * g0, z0)

        Lmax = torch.maximum(L0, ctx.loss(z, y, kind=kind, penalized=pen))
        zmax = torch.where((L0 > Lmax - 1e-15)[:, None], x_before, z)
        # per-sample adaptive-step bookkeeping
        inc_count = torch.zeros(B, dtype=torch.float64, device=device)
        Lmax_cp = Lmax.clone()
        halved_last = torch.zeros(B, dtype=torch.bool, device=device)

        W = sorted(capgd_checkpoints(n_iter))
        stage_len_of = {}
        prev_w = 0
        for w in W:
            stage_len_of[w] = w - prev_w
            prev_w = w
        prev_loss = ctx.loss(z, y, kind=kind, penalized=pen)
        for k in range(1, n_iter):                     # produce x(k+1), k=1..n_iter-1
            # gradient at x(k)
            gk = ctx.grad(z, y, kind=kind, penalized=pen)
            if ctx.normalize_grad:
                gk = gk / torch.clamp(gk.norm(dim=-1, keepdim=True), min=1e-10)
            # z(k+1) = P_S(x(k) + eta * grad)
            step = ctx.project_ball(z + eta.unsqueeze(-1) * gk, z0)
            # x(k+1) = P_S(x(k) + alpha*(z(k+1)-x(k)) + (1-alpha)*(x(k)-x(k-1)))
            z_new = ctx.project_ball(
                z + 0.75 * (step - z) + 0.25 * (z - z_prev), z0)
            z_new = ctx.repair(z_new)

            L_new = ctx.loss(z_new, y, kind=kind, penalized=pen)
            # count of increases towards condition 1 (pairs within this stage)
            inc_count += (L_new > prev_loss).to(torch.float64)
            # best iterate tracking
            better = L_new > Lmax
            zmax = torch.where(better[:, None], z_new, zmax)
            Lmax = torch.maximum(Lmax, L_new)

            z_prev, z = z, z_new
            prev_loss = L_new

            if (k + 1) in W:
                stage_len = stage_len_of[k + 1]
                # condition 1: fraction of increasing steps < rho
                cond1 = inc_count < 0.75 * stage_len
                # condition 2: step not reduced at last checkpoint AND no best-loss progress
                cond2 = (~halved_last) & ((Lmax - Lmax_cp).abs() < 1e-12)
                halve = cond1 | cond2
                eta = torch.where(halve, eta / 2.0, eta)
                inc_count.zero_()
                Lmax_cp = Lmax.clone()
                halved_last = halve

        # keep the best iterate of this start
        keep = Lmax > best_L
        best_z = torch.where(keep[:, None], zmax, best_z)
        best_L = torch.maximum(best_L, Lmax)

    return best_z


def postprocess_repair(ctx: ConstrainedAttack, z, z0):
    """Final repair + ball projection so returned examples are valid
    (integer-rounding enabled + more repair passes to converge after the
    rounding). Returns the final (feasible) standardized example."""
    z = ctx.project_ball(z, z0)
    raw = ctx._raw(z)
    raw_r = ctx.cset.repair(raw, n_passes=8, round_int=True)
    return ctx._std(raw_r)


def capgd_eval(ctx, z0, y, **kwargs):
    z = run_capgd(ctx, z0, y, **kwargs)
    return postprocess_repair(ctx, z, z0)


def cpgd_eval(ctx, z0, y, **kwargs):
    z = run_cpgd(ctx, z0, y, **kwargs)
    return postprocess_repair(ctx, z, z0)