"""Extended-training convergence study on the Mo system (mirrors the paper's
dataset-size study): fit surrogate models on the frozen Mo train split (194
configs) vs its superset data/Mo/extended/Mo930.json (930 AIMD-NVT configs),
and report energy/force MAE on the frozen Mo test set.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import energy_models as EM
import descriptors as D
from dataset import SplitData
from io_data import structure_to_arrays, config_targets

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CACHE = os.path.join(RESULTS, "_cache")
os.makedirs(CACHE, exist_ok=True)

SEED = 0


class Wrapped:
    """Adapter exposing the SplitData interface for a raw config set
    (computes descriptor gradients etc. lazily, exactly like SplitData)."""

    def __init__(self, configs):
        Gs, Es, Fs, nats, groups, carts, lats = [], [], [], [], [], [], []
        for c in configs:
            lat, frac, cart, _ = structure_to_arrays(c)
            G, _, _ = D.compute_descriptors(cart, lat)
            Gs.append(G)
            E, F = config_targets(c)
            Es.append(E)
            Fs.append(F)
            nats.append(len(G))
            groups.append(c["group"])
            carts.append(cart)
            lats.append(lat)
        self.G = np.vstack(Gs)
        self.E_cfg = np.array(Es)
        self.F_flat = np.vstack(Fs)
        self.num_atoms = np.array(nats)
        self.groups = np.array(groups)
        self.offs = np.cumsum([0] + list(nats)).astype(int)
        self.carts = carts
        self.lats = lats
        self.n_configs = len(Es)
        self._pp = {}

    @property
    def n_atoms(self):
        return len(self.G)

    def cfg(self, idx):
        s0, s1 = self.offs[idx], self.offs[idx + 1]
        Gc = self.G[s0:s1]
        if idx not in self._pp:
            i, j, u, d = D.neighbor_pairs(self.lats[idx], self.carts[idx])
            t = D.angular_triples_full(i, j, u, d, len(self.carts[idx]))
            self._pp[idx] = ((i, j, u, d), t)
        pairs, t = self._pp[idx]
        return Gc, pairs, t

    def descriptor_sums(self):
        S = np.zeros((self.n_configs, D.D))
        for idx in range(self.n_configs):
            s0, s1 = self.offs[idx], self.offs[idx + 1]
            S[idx] = self.G[s0:s1].sum(axis=0)
        return S


def main():
    print("== Mo extended-training (Mo930) convergence study ==", flush=True)
    tr194 = SplitData("Mo", "train", CACHE)
    te = SplitData("Mo", "test", CACHE)

    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "Mo", "extended", "Mo930.json")
    with open(path) as f:
        mo930 = json.load(f)
    tr930 = Wrapped(mo930)
    print(f"  Mo930: {tr930.n_configs} configs, {tr930.n_atoms} atoms", flush=True)

    spec = [
        ("linear_snap_proxy", EM.LinearEQModel(alpha=0.05, lambda_f=0.1)),
        ("kernel_gap_proxy", EM.KernelEQModel(gamma=0.003, alpha=0.01, n_basis=600, seed=SEED)),
        ("mlp_nnp_proxy", EM.MLPForceModel(hidden=(64, 64), max_iter=500, seed=SEED)),
    ]
    results = {}
    aimd_test_idx = [i for i in range(te.n_configs) if te.groups[i] == "AIMD-NVT"]
    for name, proto in spec:
        for tag, trset in [("n194", tr194), ("n930", tr930)]:
            mk = type(proto)()
            for k0, v0 in proto.params.items():
                setattr(mk, k0, v0)
            mk.params = dict(proto.params)
            if isinstance(mk, EM.LinearEQModel) and tag == "n930":
                # the 930 set is a single structure class: re-tune its ridge
                # regularization on an inner 20% holdout (energy+force score)
                rng = np.random.default_rng(SEED)
                idxs = rng.permutation(trset.n_configs)
                nval = int(round(0.2 * trset.n_configs))
                fi, vi = idxs[nval:], idxs[:nval]
                g = mk._gram(trset, fi)
                best = None
                for a in [1e-3, 1e-1, 1.0, 10.0, 100.0, 1000.0]:
                    for lf in [0.01, 0.1, 1.0]:
                        cand = EM.LinearEQModel(alpha=a, lambda_f=lf).solve_from_gram(g)
                        cE, cF, _, _ = EM.batch_metrics_eval(cand, trset, vi)
                        sc = cE + 50.0 * cF
                        if best is None or sc < best[0]:
                            best = (sc, a, lf)
                mk = EM.LinearEQModel(alpha=best[1], lambda_f=best[2])
                mk.fit(trset, list(range(trset.n_configs)))
            else:
                mk.fit(trset, list(range(trset.n_configs)))
            tr_e, tr_f, _, _ = EM.batch_metrics_eval(mk, trset, list(range(trset.n_configs)))
            te_e, te_f, _, _ = EM.batch_metrics_eval(mk, te, list(range(te.n_configs)))
            # in-domain subset of the test set (AIMD-NVT snapshots only)
            te_e_aimd, te_f_aimd, _, _ = EM.batch_metrics_eval(mk, te, aimd_test_idx)
            results[f"{name}/{tag}"] = dict(train_energy_mae=tr_e, train_force_mae=tr_f,
                                            test_energy_mae=te_e, test_force_mae=te_f,
                                            test_energy_mae_aimd=te_e_aimd,
                                            test_force_mae_aimd=te_f_aimd,
                                            params=mk.params)
            print(f"  {name:20s} {tag:5s} traE={tr_e:7.2f} meV  testE={te_e:7.2f} (AIMD:{te_e_aimd:7.2f}) "
                  f"testF={te_f:.4f} (AIMD:{te_f_aimd:.4f}) {mk.params}", flush=True)

    with open(os.path.join(RESULTS, "mo930_convergence.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Saved results/mo930_convergence.json")


if __name__ == "__main__":
    main()