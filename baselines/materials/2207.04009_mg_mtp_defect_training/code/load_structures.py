"""Shared helpers: parse MTP/ATOMSK .cfg files into structure records."""
import numpy as np


def parse_cfg_file(path):
    """Parse a .cfg file; return list of dicts (one per structure)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    recs = []
    i, n = 0, len(lines)
    while i < n:
        if lines[i].strip() != "BEGIN_CFG":
            i += 1
            continue
        j = i + 1
        while j < n and "Size" not in lines[j]:
            j += 1
        j += 1
        size = int(lines[j].strip())
        while j < n and "SuperCell" not in lines[j]:
            j += 1
        cell = np.array(
            [list(map(float, lines[k].split())) for k in range(j + 1, j + 4)]
        )
        j += 4
        while j < n and "AtomData:" not in lines[j]:
            j += 1
        j += 1
        pos = np.zeros((size, 3))
        forces = np.zeros((size, 3))
        types = np.zeros(size, dtype=int)
        for a in range(size):
            toks = lines[j].split()
            types[a] = int(toks[1])
            pos[a] = [float(toks[2]), float(toks[3]), float(toks[4])]
            forces[a] = [float(toks[5]), float(toks[6]), float(toks[7])]
            j += 1
        energy = None
        while j < n and "Energy" not in lines[j]:
            j += 1
        if j < n:
            energy = float(lines[j].split("\t")[-1].split()[-1])
            j += 1
        stress = np.full(6, np.nan)
        has_stress = False
        while j < n and "PlusStress" not in lines[j]:
            j += 1
        if j < n and j + 1 < n:
            toks = lines[j + 1].split()
            if len(toks) >= 6:
                stress = np.array(list(map(float, toks[:6])))
                has_stress = True
            j += 2
        feature = None
        while j < n and "Feature" not in lines[j]:
            j += 1
        if j < n:
            feature = lines[j].split()[-1].strip()
            j += 1
        recs.append(
            {
                "n_atoms": size,
                "cell": cell,
                "positions": pos,
                "forces": forces,
                "types": types,
                "energy": energy,
                "stress": stress,
                "has_stress": has_stress,
                "feature": feature,
            }
        )
        while i < n and lines[i].strip() != "END_CFG":
            i += 1
        i += 1
    return recs


def load_cfg_structures(path):
    return parse_cfg_file(path)
