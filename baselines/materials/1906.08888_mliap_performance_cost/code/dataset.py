"""Per-element dataset: extract descriptors for all configs of a frozen
train/test split and cache to disk. Pairs/triples for the exact descriptor
gradients are recomputed lazily per config (cheap) to keep caches small.
"""
import os
import pickle

import numpy as np

import descriptors as D
from io_data import load_configs, structure_to_arrays, config_targets


class SplitData:
    """All per-config descriptor data for one (element, split) bundle."""

    def __init__(self, element, split, cache_dir, force_recompute=False):
        self.element = element
        self.split = split
        cache = os.path.join(cache_dir, f"{element}_{split}_desc.npz")
        pk = os.path.join(cache_dir, f"{element}_{split}_geom.pkl")
        if not force_recompute and os.path.exists(cache):
            self._load_cache(cache, pk)
            return
        self._build_and_save(cache, pk)

    # ------------------------------------------------------------------ build
    def _build_and_save(self, cache, pk):
        cfgs = load_configs(self.element, self.split)
        Gs, E_cfg, F_flat, num_atoms, groups = [], [], [], [], []
        carts, lats = [], []
        for c in cfgs:
            lat, frac, cart, _ = structure_to_arrays(c)
            G, _, _ = D.compute_descriptors(cart, lat)
            Gs.append(G)
            E, F = config_targets(c)
            E_cfg.append(E)
            F_flat.append(F)
            num_atoms.append(len(G))
            groups.append(c["group"])
            carts.append(cart)
            lats.append(lat)
        self.G = np.vstack(Gs)
        self.E_cfg = np.asarray(E_cfg)
        self.F_flat = np.vstack(F_flat)
        self.num_atoms = np.asarray(num_atoms)
        self.groups = np.asarray(groups)
        self.offs = np.cumsum([0] + list(num_atoms)).astype(int)
        self.carts = carts
        self.lats = lats
        self._pp = {}
        np.savez(cache, G=self.G, E_cfg=self.E_cfg, F_flat=self.F_flat,
                 num_atoms=self.num_atoms, offs=self.offs, groups=self.groups)
        with open(pk, "wb") as f:
            pickle.dump((carts, lats), f)

    def _load_cache(self, cache, pk):
        z = np.load(cache, allow_pickle=True)
        self.G = z["G"]
        self.E_cfg = z["E_cfg"]
        self.F_flat = z["F_flat"]
        self.num_atoms = z["num_atoms"]
        self.groups = z["groups"]
        self.offs = z["offs"]
        with open(pk, "rb") as f:
            self.carts, self.lats = pickle.load(f)
        self._pp = {}

    @property
    def n_configs(self):
        return len(self.E_cfg)

    @property
    def n_atoms(self):
        return len(self.G)

    # ----------------------------------------------------------------- access
    def cfg(self, idx):
        """(G_cfg, pairs_info, triples_info) for config idx."""
        s0, s1 = self.offs[idx], self.offs[idx + 1]
        Gc = self.G[s0:s1]
        if idx not in self._pp:
            i, j, u, d = D.neighbor_pairs(self.lats[idx], self.carts[idx])
            t = D.angular_triples_full(i, j, u, d, len(self.carts[idx]))
            self._pp[idx] = ((i, j, u, d), t)
        pairs, t = self._pp[idx]
        return Gc, pairs, t

    def descriptor_sums(self):
        M = len(self.E_cfg)
        S = np.zeros((M, D.D))
        for idx in range(M):
            s0, s1 = self.offs[idx], self.offs[idx + 1]
            S[idx] = self.G[s0:s1].sum(axis=0)
        return S