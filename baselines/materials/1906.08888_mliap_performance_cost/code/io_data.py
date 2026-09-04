"""Load frozen ML-IAP JSON configs (dataset of 1906.08888).

Each config entry has:
  structure   : pymatgen Structure dict (lattice + sites)
  num_atoms   : int
  element     : str
  group       : str (Vacancy / Interstitial / Surface / Elastic / AIMD-NVT ...)
  outputs     : {energy: eV, forces: [[fx,fy,fz], ...] eV/A}
  tag         : train / test
  description : str
"""
import json
import os

import numpy as np

DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data")

ELEMENTS = ["Li", "Mo", "Cu", "Ni", "Si", "Ge"]


def load_configs(element, split):
    """Return list of config dicts from data/<element>/<split>.json.
    `split` may be 'train' (alias) or 'training' and 'test'."""
    if split == "train":
        split = "training"
    path = os.path.join(DATA_ROOT, element, f"{split}.json")
    with open(path) as f:
        return json.load(f)


def load_mo930():
    path = os.path.join(DATA_ROOT, "Mo", "extended", "Mo930.json")
    with open(path) as f:
        return json.load(f)


def structure_to_arrays(cfg):
    """Extract lattice matrix, fractional coords, cartesian coords from a config."""
    s = cfg["structure"]
    lat = np.asarray(s["lattice"]["matrix"], dtype=float)  # rows = lattice vectors
    sites = s["sites"]
    names = [site["species"][0]["element"] for site in sites]
    frac = np.asarray([site["abc"] for site in sites], dtype=float)
    cart = frac @ lat
    return lat, frac, cart, np.array(names)


def config_targets(cfg):
    """Return (E_tot eV, F flat eV/A Nx3)."""
    E = float(cfg["outputs"]["energy"])
    F = np.asarray(cfg["outputs"]["forces"], dtype=float)
    return E, F


def load_element_arrays(element):
    """Load train/test (E, F, num_atoms, group, cart, lat) for an element."""
    out = {}
    for split in ["train", "test"]:
        cfgs = load_configs(element, split)
        Es, Fs, nat, groups, carts, lats = [], [], [], [], [], []
        for c in cfgs:
            E, F = config_targets(c)
            lat, _, cart, _ = structure_to_arrays(c)
            Es.append(E)
            Fs.append(F)
            nat.append(c["num_atoms"])
            groups.append(c["group"])
            carts.append(cart)
            lats.append(lat)
        out[split] = dict(
            Es=np.array(Es, dtype=float),
            Fs=np.vstack(Fs),
            num_atoms=np.array(nat, dtype=int),
            groups=np.array(groups),
            carts=carts,
            lats=lats,
            n_configs=len(cfgs),
            n_atoms=int(np.sum(nat)),
        )
    return out


def sample_config_stats(element="Mo", split="train", idx=0):
    """Dump one config's raw numbers for evidence cross-check."""
    cfg = load_configs(element, split)[idx]
    E, F = config_targets(cfg)
    return {
        "element": element,
        "split": split,
        "index": idx,
        "group": cfg["group"],
        "num_atoms": cfg["num_atoms"],
        "energy_eV": float(E),
        "forces_eV_ang": F.tolist(),
        "structure_json": cfg["structure"],
    }