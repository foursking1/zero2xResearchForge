"""Trainable surrogate ML-IAP energy/force models over the frozen train/test
splits. All energy-conserving models are fitted on per-config total energies
and predict forces exactly as F = -dE/dr via the descriptor-gradient
machinery (like linear SNAP / GAP); the MLP predicts forces directly.

Leakage-safe protocol:
  1. frozen train is split into fit (80%) / validation (20%) config indices
     with a fixed seed; hyper-parameters are chosen on validation only;
  2. winning hyper-parameters are refitted on the *full* frozen train set;
  3. the frozen test set is used exactly once for the final metrics.
"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor

import descriptors as D

dE_dr_radial = D.dE_dr_radial
dE_dr_angular = D.dE_dr_angular


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------
def _ridge_solve(Z, y, alpha):
    A = Z.T @ Z + alpha * np.eye(Z.shape[1])
    b = Z.T @ y
    return np.linalg.solve(A, b)


def _design_split(n_train, val_frac=0.2, seed=0):
    """Deterministic (fit_idx, val_idx) partition of config indices."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n_train)
    nval = int(round(val_frac * n_train))
    return idx[nval:], idx[:nval]


def yref_energy(feat, cfg_indices):
    nat = feat.num_atoms[cfg_indices]
    return float(np.average(feat.E_cfg[cfg_indices] / nat))


def energy_and_force_from_weights(pairs, triples, weights_cfg, num_atoms, const_per_atom):
    E, F = D.energy_and_force_from_weights(pairs, triples, weights_cfg)
    return E + const_per_atom * num_atoms, F


def batch_metrics_eval(model, feat, cfg_indices):
    """Return (mae_e_meV_per_atom, mae_f_eV_ang, per_cfg_list, F_all_cfgs)."""
    per_cfg = []
    F_preds = []
    for idx in cfg_indices:
        E, F = model.predict_config(feat, idx)
        n = int(feat.num_atoms[idx])
        per_cfg.append(abs(E - float(feat.E_cfg[idx])) / n * 1000.0)
        F_preds.append(F)
    F_flat = np.vstack(F_preds)
    tr = np.concatenate([feat.F_flat[feat.offs[idx]:feat.offs[idx + 1]] for idx in cfg_indices])
    mae_f = float(np.abs(F_flat - tr).mean())
    return float(np.mean(per_cfg)), mae_f, per_cfg, F_flat


# ---------------------------------------------------------------------------
# linear SNAP proxy (radial + angular Behler-Parrinello features, linear out)
# ---------------------------------------------------------------------------
class LinearEQModel:
    """SNAP-class linear readout fitted jointly to total energies *and*
    forces (force matching), like real SNAP potentials. Energy is conserved
    by construction (F = -dE/dr from the descriptor-gradient machinery).

    The force-fit system is linear in the coefficients, so the Gram pieces
    are computed once and hyper-parameter candidates solved cheaply.
    """

    name = "linear_snap_proxy"

    def __init__(self, alpha=1e-3, lambda_f=0.3):
        self.alpha = alpha
        self.lambda_f = lambda_f
        self.c = None          # (D,) original-feature-space per-atom weights
        self.b_const = 0.0     # per-atom constant
        self.mu = None
        self.sd = None
        self.params = dict(alpha=alpha, lambda_f=lambda_f)

    def _per_config_force_jacobian(self, Gc, pairs, t):
        """J matrix (3N, D): columns are dE/dr of each descriptor feature
        (energy gradient), so F_pred(atom,d) = -sum_m c_m J[atom*3+d, m]."""
        n = len(Gc)
        J = np.zeros((3 * n, D.D))
        for m in range(D.NR):
            W = np.zeros((n, D.D))
            W[:, m] = 1.0
            Gx, _ = dE_dr_radial(pairs, W)
            J[:, m] = Gx.ravel()
        if t is not None:
            for a in range(D.NA):
                W = np.zeros((n, D.D))
                W[:, D.NR + a] = 1.0
                Gx, _ = dE_dr_angular(t, W)
                J[:, D.NR + a] = Gx.ravel()
        return J

    def _gram(self, feat, cfg_indices):
        """Energy rows (M,D+1) + force Jacobian rows (3Ntot,D) + targets."""
        Gsums, nat = [], []
        J_list, yF_list = [], []
        for ci in cfg_indices:
            s0, s1 = feat.offs[ci], feat.offs[ci + 1]
            Gc, pairs, t = feat.cfg(ci)
            Gsums.append(Gc.sum(axis=0))
            nat.append(float(feat.num_atoms[ci]))
            J_list.append(self._per_config_force_jacobian(Gc, pairs, t))
            yF_list.append(feat.F_flat[s0:s1].ravel())
        ZE = np.hstack([np.vstack(Gsums), np.asarray(nat)[:, None]])
        return dict(ZE=ZE,
                    yE=feat.E_cfg[cfg_indices],
                    J=np.vstack(J_list),
                    yF=np.concatenate(yF_list),
                    nat=np.asarray(nat))

    def solve_from_gram(self, g):
        """Solve the joint energy+force ridge with self.alpha/lambda_f."""
        ZE, yE, J, yF = g["ZE"], g["yE"], g["J"], g["yF"]
        self.mu = ZE[:, :D.D].mean(axis=0)
        self.sd = np.where(ZE[:, :D.D].std(axis=0) > 1e-6, ZE[:, :D.D].std(axis=0), 1.0)
        Zs = np.hstack([(ZE[:, :D.D] - self.mu) / self.sd, ZE[:, D.D:]])  # (M,p)
        lf = self.lambda_f
        p = Zs.shape[1]
        # normal equations with precomputed pieces (force rows do not see
        # the per-atom constant column, so G1 is embedded in the feature block)
        G0 = Zs.T @ Zs
        Js = J / self.sd[None, :]
        G1f = Js.T @ Js
        G1 = np.zeros((p, p))
        G1[:D.D, :D.D] = G1f
        t0 = Zs.T @ yE
        t1f = Js.T @ yF
        t1 = np.zeros(p)
        t1[:D.D] = t1f
        Gram = G0 + lf * lf * G1 + self.alpha * np.eye(p)
        rhs = t0 + lf * lf * t1
        coef = np.linalg.solve(Gram, rhs)
        self.c = coef[:-1] / self.sd
        self.b_const = float(coef[-1]) - float(coef[:-1] @ (self.mu / self.sd))
        return self

    def fit(self, feat, cfg_indices):
        g = self._gram(feat, cfg_indices)
        return self.solve_from_gram(g)

    def predict_config(self, feat, idx):
        s0, s1 = feat.offs[idx], feat.offs[idx + 1]
        N = s1 - s0
        Gc, pairs, t = feat.cfg(idx)
        w = np.tile(self.c, (N, 1))
        E, F = D.energy_and_force_from_weights(pairs, t, w)
        E = E + self.b_const * feat.num_atoms[idx]
        return E, F

    def predict_energy_only(self, feat, idx):
        s0, s1 = feat.offs[idx], feat.offs[idx + 1]
        Gc, pairs, t = feat.cfg(idx)
        w = np.tile(self.c, (s1 - s0, 1))
        E = D.energy_radial(pairs, w)
        if t is not None:
            _, Ea = dE_dr_angular(t, w)
            E += Ea
        return E + self.b_const * feat.num_atoms[idx]


class QuadEQModel:
    name = "quad_snap_proxy"

    def __init__(self, alpha=1e-4):
        self.alpha = alpha
        self.DD2 = D.D * (D.D + 1) // 2
        self.c1 = None          # (D,) original-space linear part
        self.c1s = None         # scaled linear coefficients
        self.cp = None          # scaled product coefficients per pair
        self.Q = None           # symmetric (D,D) scaled matrix for gradient
        self.b_const = 0.0
        self.er = 0.0
        self.mu = None
        self.sd = None
        self.params = dict(alpha=alpha)
        self.pairs_idx = [(a, b) for a in range(D.D) for b in range(a, D.D)]

    def _scaled_atom_features(self, G):
        g = (G - self.mu) / self.sd
        X = np.empty((len(G), D.D + self.DD2))
        X[:, :D.D] = g
        k = D.D
        for a, b in self.pairs_idx:
            X[:, k] = g[:, a] * g[:, b]
            k += 1
        return X

    def fit(self, feat, cfg_indices):
        nat = feat.num_atoms[cfg_indices]
        atoms = np.concatenate([np.arange(feat.offs[ci], feat.offs[ci + 1]) for ci in cfg_indices])
        Gfit = feat.G[atoms]
        self.mu = Gfit.mean(axis=0)
        self.sd = np.where(Gfit.std(axis=0) > 1e-6, Gfit.std(axis=0), 1.0)
        X = self._scaled_atom_features(Gfit)
        S = np.zeros((len(cfg_indices), X.shape[1]))
        cur = 0
        for q, ci in enumerate(cfg_indices):
            na = nat[q]
            S[q] = X[cur:cur + na].sum(axis=0)
            cur += na
        Z = np.hstack([S, nat[:, None]])
        self.er = yref_energy(feat, cfg_indices)
        y = feat.E_cfg[cfg_indices] - self.er * nat
        coef = _ridge_solve(Z, y, self.alpha)
        self.c1s = coef[:D.D]
        self.c1 = self.c1s / self.sd
        self.cp = coef[D.D:-1].copy()
        self.b_dash = float(coef[-1])
        self.b_const = self.er + self.b_dash
        return self

    def predict_config(self, feat, idx):
        s0, s1 = feat.offs[idx], feat.offs[idx + 1]
        N = s1 - s0
        Gc, pairs, t = feat.cfg(idx)
        g = (Gc - self.mu) / self.sd
        X = self._scaled_atom_features(Gc)
        E = float(X.sum(axis=0) @ np.concatenate([self.c1s, self.cp])) + self.b_const * feat.num_atoms[idx]
        grad_quad = np.zeros((N, D.D))
        for q, (a, b) in enumerate(self.pairs_idx):
            cc = self.cp[q]
            if a == b:
                grad_quad[:, a] += 2 * cc * g[:, a]
            else:
                grad_quad[:, a] += cc * g[:, b]
                grad_quad[:, b] += cc * g[:, a]
        w = self.c1[None, :] + grad_quad / self.sd[None, :]
        _, F = D.energy_and_force_from_weights(pairs, t, w)
        return E, F


# ---------------------------------------------------------------------------
# sparse kernel (GAP proxy): kernel ridge over per-atom descriptors
# ---------------------------------------------------------------------------
def cdist_sq(A, B):
    a2 = (A ** 2).sum(axis=1)[:, None]
    b2 = (B ** 2).sum(axis=1)[None, :]
    return np.clip(a2 + b2 - 2.0 * A @ B.T, 0.0, None)


class KernelEQModel:
    name = "kernel_gap_proxy"

    def __init__(self, gamma=0.05, alpha=1e-4, n_basis=700, seed=42):
        self.gamma = gamma
        self.alpha = alpha
        self.n_basis = n_basis
        self.seed = seed
        self.scaler = None
        self.Xb = None
        self.alpha_k = None
        self.bn = 0.0
        self.b1 = 0.0
        self.params = dict(gamma=gamma, alpha=alpha, n_basis=n_basis)

    def _kernel_rows(self, X):
        """(N,B) RBF on scaled descriptors."""
        with np.errstate(over="ignore", under="ignore"):
            k = np.exp(-self.gamma * cdist_sq(self.scaler.transform(np.asarray(X, dtype=float)), self.Xb))
        return k

    def fit(self, feat, cfg_indices):
        rng = np.random.default_rng(self.seed)
        # atoms belonging to the fitting configs only (strict protocol)
        atoms = np.concatenate([np.arange(feat.offs[ci], feat.offs[ci + 1]) for ci in cfg_indices])
        B = min(self.n_basis, len(atoms))
        b_atoms = atoms[rng.choice(len(atoms), size=B, replace=False)]
        self.scaler = StandardScaler().fit(feat.G[atoms])
        self.Xb = self.scaler.transform(feat.G[b_atoms])
        K = np.zeros((len(cfg_indices), B))
        for q, ci in enumerate(cfg_indices):
            s0, s1 = feat.offs[ci], feat.offs[ci + 1]
            K[q] = self._kernel_rows(feat.G[s0:s1]).sum(axis=0)
        nat = feat.num_atoms[cfg_indices]
        Z = np.hstack([K, nat[:, None], np.ones((len(cfg_indices), 1))])
        coef = _ridge_solve(Z, feat.E_cfg[cfg_indices], self.alpha)
        self.alpha_k = coef[:B].copy()
        self.bn = float(coef[B])
        self.b1 = float(coef[B + 1])
        return self

    def predict_config(self, feat, idx):
        Gc, pairs, t = feat.cfg(idx)
        s0, s1 = feat.offs[idx], feat.offs[idx + 1]
        N = s1 - s0
        kM = self._kernel_rows(Gc)                       # (N,B)
        E = float(self.alpha_k @ kM.sum(axis=0)) + self.bn * feat.num_atoms[idx] + self.b1
        diff = self.scaler.transform(Gc)[:, None, :] - self.Xb[None, :, :]   # (N,B,D)
        att = kM * self.alpha_k[None, :]                 # (N,B)
        W = -2.0 * self.gamma * (att[:, :, None] * diff).sum(axis=1)          # (N,D) scaled
        Wf = W / self.scaler.scale_[None, :]             # feature-space weights
        _, F = D.energy_and_force_from_weights(pairs, t, Wf)
        return E, F


# ---------------------------------------------------------------------------
# MLP (NNP proxy): per-atom features -> force head + energy head (direct fit)
# ---------------------------------------------------------------------------
class MLPForceModel:
    name = "mlp_nnp_proxy"

    def __init__(self, hidden=(64, 64), max_iter=400, alpha=1e-3, seed=7):
        self.hidden = hidden
        self.max_iter = max_iter
        self.alpha_reg = alpha
        self.seed = seed
        self.scalerF = None
        self.scalerE = None
        self.mlpF = None
        self.mlpE = None
        self.er = 0.0
        self.params = dict(hidden=hidden, max_iter=max_iter, alpha=alpha)

    def fit(self, feat, cfg_indices):
        atoms = np.concatenate([np.arange(feat.offs[ci], feat.offs[ci + 1]) for ci in cfg_indices])
        X = feat.G[atoms]
        Fy = feat.F_flat[atoms]
        e_per = feat.E_cfg[cfg_indices] / feat.num_atoms[cfg_indices] - yref_energy(feat, cfg_indices)
        ey = np.concatenate([np.full(feat.num_atoms[ci], e_per[q]) for q, ci in enumerate(cfg_indices)])
        self.scalerF = StandardScaler().fit(X)
        self.scalerE = StandardScaler().fit(X)
        self.mlpF = MLPRegressor(hidden_layer_sizes=self.hidden, solver="adam", alpha=self.alpha_reg,
                                 max_iter=self.max_iter, early_stopping=True, validation_fraction=0.12,
                                 n_iter_no_change=15, random_state=self.seed)
        self.mlpF.fit(self.scalerF.transform(X), Fy)
        self.mlpE = MLPRegressor(hidden_layer_sizes=self.hidden, solver="adam", alpha=self.alpha_reg,
                                 max_iter=self.max_iter, early_stopping=True, validation_fraction=0.12,
                                 n_iter_no_change=15, random_state=self.seed)
        self.mlpE.fit(self.scalerE.transform(X), ey)
        self.er = yref_energy(feat, cfg_indices)
        return self

    def predict_config(self, feat, idx):
        s0, s1 = feat.offs[idx], feat.offs[idx + 1]
        Gc = feat.G[s0:s1]
        F = self.mlpF.predict(self.scalerF.transform(Gc))
        E = float(self.mlpE.predict(self.scalerE.transform(Gc)).sum()) + self.er * feat.num_atoms[idx]
        return E, F