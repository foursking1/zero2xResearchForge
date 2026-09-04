"""Comparative-network construction and generic bound propagation.

The paper's comparative encoding evaluates the policy twice:  f(x)  and  f(x+s),
stacked into a single 12-dim output.  We build that as a sequential ReLU network
in the concatenated input  u = [x ; s]  (96 dims) and implement:

- forward evaluation (exact, used by every backend),
- interval bound propagation (IBP),
- CROWN-style linear-relaxation lower/upper bounds of an output functional,
- the MIP (HiGHS) encoding and the CROWN/IBP branch-and-bound backend.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .model import ReLUNet


@dataclass
class CompNet:
    """Comparative network: input u=[x;s] (96-dim), output 12-dim = [f(x); f(x+s)]."""

    Ws: list[np.ndarray]      # list of weight matrices, layer 0..L-1
    bs: list[np.ndarray]
    relu: list[bool]          # is layer followed by ReLU
    masks: list[np.ndarray | None]  # per-layer ReLU row mask (None = all rows)

    @property
    def n_in(self) -> int:
        return self.Ws[0].shape[1]

    @property
    def n_out(self) -> int:
        return self.Ws[-1].shape[0]

    def forward(self, u: np.ndarray) -> np.ndarray:
        u = np.asarray(u, dtype=np.float64)
        h = u
        for W, b, is_relu, mask in zip(self.Ws, self.bs, self.relu, self.masks):
            z = h @ W.T + b
            if is_relu:
                if mask is None:
                    h = np.maximum(0.0, z)
                else:
                    h = np.where(mask, np.maximum(0.0, z), z)
            else:
                h = z
        return h

    def forward_layers(self, u: np.ndarray) -> list[np.ndarray]:
        """Return per-layer activations (pre-activation for linear layers)."""
        h = np.asarray(u, dtype=np.float64)
        acts = [h]
        for W, b, is_relu, mask in zip(self.Ws, self.bs, self.relu, self.masks):
            z = h @ W.T + b
            if is_relu:
                if mask is None:
                    h = np.maximum(0.0, z)
                else:
                    h = np.where(mask, np.maximum(0.0, z), z)
            else:
                h = z
            acts.append(h)
        return acts


def reduce_net_for_box(net: CompNet, lo: np.ndarray, hi: np.ndarray) -> tuple[CompNet, np.ndarray, np.ndarray]:
    """Eliminate fixed input coordinates: returns a network on the varying dims.

    lo, hi are the full input bounds.  The reduced network's input is x_v with
    box [lo[V], hi[V]] where V are the varying (lo < hi) coordinates.
    """
    lo = np.asarray(lo, dtype=np.float64)
    hi = np.asarray(hi, dtype=np.float64)
    vary = np.where(hi - lo > 1e-12)[0]
    fixed = np.where(hi - lo <= 1e-12)[0]
    W0 = net.Ws[0]
    b0 = net.bs[0].copy()
    if fixed.size:
        b0 = b0 + W0[:, fixed] @ lo[fixed]
    W0r = W0[:, vary]
    Ws = [W0r] + net.Ws[1:]
    red = CompNet(Ws=Ws, bs=net.bs, relu=net.relu, masks=net.masks)
    return red, lo[vary], hi[vary]


def build_comparative(net: ReLUNet) -> CompNet:
    """Build the comparative (two-copy) network from a single policy net."""
    W0, b0 = net.W0, net.b0
    W1, b1 = net.W1, net.b1
    W2, b2 = net.W2, net.b2
    H0, H1 = W0.shape[0], W1.shape[0]
    n_in = net.n_in

    # copy1 reads x (first n_in cols), copy2 reads x + s  =>  [W, W] on [x;s]
    Z0a = np.concatenate([W0, np.zeros_like(W0)], axis=1)       # (H0, 2n)
    Z0b = np.concatenate([W0, W0], axis=1)                      # (H0, 2n)
    W0c = np.concatenate([Z0a, Z0b], axis=0)                    # (2H0, 2n)
    b0c = np.concatenate([b0, b0])

    W1c = np.zeros((2 * H1, 2 * H0))
    W1c[:H1, :H0] = W1
    W1c[H1:, H0:] = W1
    b1c = np.concatenate([b1, b1])

    W2c = np.zeros((12, 2 * H1))
    W2c[:6, :H1] = W2
    W2c[6:, H1:] = W2
    b2c = np.concatenate([b2, b2])

    mask0c = np.concatenate([net.mask0, net.mask0])

    return CompNet(
        Ws=[W0c, W1c, W2c],
        bs=[b0c, b1c, b2c],
        relu=[True, True, False],
        masks=[mask0c, None, None],
    )


def ibp_bounds(net: CompNet, lo: np.ndarray, hi: np.ndarray):
    """Interval bound propagation over the box [lo, hi].

    Returns ``pre``: a list whose element k holds the bounds of the *input to
    layer k*::

        pre[0]      = input box
        pre[k>=1]   = bounds of the pre-activation z_k (for ReLU layers) or the
                      output y (for the final linear layer)
    """
    lo = np.asarray(lo, dtype=np.float64)
    hi = np.asarray(hi, dtype=np.float64)
    pre = [(lo, hi)]
    for W, b, is_relu, mask in zip(net.Ws, net.bs, net.relu, net.masks):
        Wp = np.maximum(W, 0.0)
        Wn = np.minimum(W, 0.0)
        zlo = Wp @ lo + Wn @ hi + b
        zhi = Wp @ hi + Wn @ lo + b
        pre.append((zlo, zhi))
        if is_relu:
            if mask is None:
                lo = np.maximum(0.0, zlo)
                hi = np.maximum(0.0, zhi)
            else:
                lo = np.where(mask, np.maximum(0.0, zlo), zlo)
                hi = np.where(mask, np.maximum(0.0, zhi), zhi)
        else:
            lo, hi = zlo, zhi
    return pre


def crown_bound(net: CompNet, lo: np.ndarray, hi: np.ndarray, c: np.ndarray) -> tuple[float, float]:
    """CROWN-style sound bounds of the linear functional  c^T y  over the input box.

    Returns (lower_bound, upper_bound).  ReLU layers are relaxed with the standard
    convex hull.  For the lower bound direction with a positive coefficient on an
    unstable neuron we take the best of the two valid relaxations  h >= z  and
    h >= 0;  for the upper direction we use the chord  h <= (u/(u-l))(z-l).
    """
    pre = ibp_bounds(net, lo, hi)  # pre[k+1] = pre-activation bounds of layer k
    L = len(net.Ws)
    c = np.asarray(c, dtype=np.float64)

    def prop(direction: str, pos_slope: float, cvec: np.ndarray) -> float:
        """Return bound of cvec^T y.  pos_slope is the slope used for the lower
        relaxation of unstable neurons with a positive coefficient (1 -> h>=z,
        0 -> h>=0)."""
        g = cvec.copy()
        const = 0.0
        for k in range(L - 1, -1, -1):
            W = net.Ws[k]
            b = net.bs[k]
            is_relu = net.relu[k]
            mask = net.masks[k]
            zlo, zhi = pre[k + 1]
            if not is_relu:
                # y_k = W h_{k-1} + b  =>  coeff on h_{k-1} = W^T g, const += b^T g
                const += float(b @ g)
                g = W.T @ g
                continue
            # ReLU layer: g is the coefficient on h_k = relu(z_k)
            gg = np.zeros_like(g)
            cc = 0.0
            for i in range(g.size):
                gi = g[i]
                if gi == 0.0:
                    continue
                li, ui = zlo[i], zhi[i]
                if mask is not None and not mask[i]:
                    gg[i] = gi
                    continue
                if li >= 0.0:
                    gg[i] = gi
                elif ui <= 0.0:
                    gg[i] = 0.0
                else:
                    if gi > 0.0:
                        if direction == "lo":
                            gg[i] = gi * pos_slope
                        else:  # upper bound needs upper relax of h
                            alpha = ui / (ui - li)
                            beta = -alpha * li
                            gg[i] = gi * alpha
                            cc += gi * beta
                    else:  # gi < 0
                        if direction == "hi":
                            # upper bound, negative coeff -> lower relax h>=z (slope 1)
                            gg[i] = gi
                        else:  # lower bound, negative coeff -> upper relax chord
                            alpha = ui / (ui - li)
                            beta = -alpha * li
                            gg[i] = gi * alpha
                            cc += gi * beta
            # z_k = W h_{k-1} + b  =>  coeff on h_{k-1} = W^T gg, const += b^T gg + cc
            const += float(b @ gg) + cc
            g = W.T @ gg
        # final linear functional g^T u + const over the input box
        if direction == "lo":
            return float(g @ np.where(g >= 0, lo, hi) + const)
        else:
            return float(g @ np.where(g >= 0, hi, lo) + const)

    lb = max(prop("lo", 1.0, c), prop("lo", 0.0, c))
    ub = prop("hi", 1.0, c)
    return lb, ub
