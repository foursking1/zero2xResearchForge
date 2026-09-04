# -*- coding: utf-8 -*-
"""DASH frozen-data parsing and label matching (arXiv:1903.02557).

Loads the frozen OzDES spectra (.dat) and the ATel label table
(all_atels.txt), matches each .dat to its ATel row by the object name, and
normalises the ATel labels to the paper's broad classes (Ia / II / Ibc; '?'
kept as an uncertain member of that broad class; Ic-broad reported separately).

This module performs NO machine-learning / DASH classification -- it only
extracts the frozen data facts needed for the L1 verification.
"""
import os
import csv
import re
import json
import glob
import numpy as np

# Path to the frozen data (hosted outside the task dir; see data/DATA_LOCATION.md)
DATA_ROOT = os.path.normpath(os.environ.get(
    "DASH_DATA_ROOT",
    "F:/dataset/astro/1903.02557_dash_supernova_class"))
OZDES = os.path.join(DATA_ROOT, "OzDES_data")
ATEL_FILE = os.path.join(OZDES, "all_atels.txt")

# Paper Table 1 broad-class mapping (Muthukrishna et al. 2019, Sec.5.2)
SN_BROAD = {
    "Ia": {"Ia-norm", "Ia-91T", "Ia-91bg", "Ia-csm", "Ia-02cx", "Ia-pec"},
    "II": {"IIP", "IIL", "IIn"},
    "Ibc": {"Ib-norm", "Ibn", "IIb", "Ib-pec", "Ic-norm", "Ic-broad", "Ic-pec"},
}


def atel_to_broad(atype):
    """Map an ATel / DASH type string to (broad, uncertain, is_icbroad).

    broad: 'Ia' | 'II' | 'Ibc' | 'SLSN' | 'Other' | None
    uncertain: True if the original label carried a '?'.
    """
    t = str(atype).strip()
    unc = t.endswith("?")
    base = t.rstrip("? ").strip()
    if base.startswith("SN"):
        base = base[2:]
    base = base.strip()
    # Ic-broad is a special DASH subclass (host contamination, paper Sec.5.2)
    if base == "Ic-broad":
        return "Ibc", unc, True
    if base in SN_BROAD["Ia"]:
        return "Ia", unc, False
    if base in SN_BROAD["II"]:
        return "II", unc, False
    if base in SN_BROAD["Ibc"]:
        return "Ibc", unc, False
    # plain class names
    if base in ("Ia", "Ib", "Ic"):
        return base if base != "Ib" else "Ibc", unc, False
    if base in ("II", "II-P", "IIP"):
        return "II", unc, False
    if base in ("SLSN-I", "SLSN"):
        return "SLSN", unc, False
    if base in ("Ibc", "Ib/c"):
        return "Ibc", unc, False
    return None, unc, False


def read_atels():
    """Return list of ATel row dicts (all entries in all_atels.txt)."""
    rows = []
    with open(ATEL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) < 9:
                continue
            if parts[0].strip() == "Name":
                continue
            rows.append({
                "name": parts[0].strip(),
                "ra": parts[1].strip(),
                "dec": parts[2].strip(),
                "disc_date": parts[3].strip(),
                "disc_mag": parts[4].strip(),
                "spec_date": parts[5].strip(),
                "redshift": parts[6].strip(),
                "type": parts[7].strip(),
                "phase": parts[8].strip(),
                "notes": parts[9].strip() if len(parts) > 9 else "",
            })
    return rows


def find_dat_files():
    return sorted(glob.glob(os.path.join(OZDES, "ATEL_*", "*.dat")))


def name_from_file(path):
    return os.path.splitext(os.path.basename(path))[0].split("_")[0]


def build_spectrum_table():
    """Match every .dat spectrum to its ATel row.

    Returns (list_of_dict, stats).
    Each dict has: file, obj, epoch, atel_type, broad, uncertain, icbroad,
    redshift (float or None), phase.
    """
    atels = read_atels()
    by_name = {}
    for a in atels:
        by_name.setdefault(a["name"], []).append(a)

    dats = find_dat_files()
    spectra = []
    unmatched = []
    for path in dats:
        obj = name_from_file(path)
        cands = by_name.get(obj, [])
        if not cands:
            # try case-insensitive / whitespace-normalised
            cands = [a for a in atels if a["name"].replace(" ", "").lower() == obj.lower()]
        if not cands:
            unmatched.append(path)
            spectra.append({
                "file": path, "obj": obj, "epoch": None, "atel_type": None,
                "broad": None, "uncertain": False, "icbroad": False,
                "redshift": None, "phase": None, "matched": False,
            })
            continue
        a = cands[0]
        try:
            z = float(a["redshift"])
        except ValueError:
            z = None
        broad, unc, icb = atel_to_broad(a["type"])
        spectra.append({
            "file": path, "obj": obj,
            "epoch": os.path.basename(path).split("_")[1] if len(os.path.basename(path).split("_")) > 1 else None,
            "atel_type": a["type"], "broad": broad, "uncertain": unc,
            "icbroad": icb, "redshift": z, "phase": a["phase"],
            "matched": True,
        })

    # stats: label distribution over the 69 spectra
    from collections import Counter
    broad_counter = Counter()
    for s in spectra:
        if s["broad"]:
            key = s["broad"] + ("?" if s["uncertain"] else "")
        else:
            key = "UNMATCHED"
        broad_counter[key] += 1
    stats = {
        "n_spectra": len(spectra),
        "n_matched": sum(s["matched"] for s in spectra),
        "n_unmatched": len(unmatched),
        "n_unique_objects": len({s["obj"] for s in spectra}),
        "broad_label_dist": dict(broad_counter),
        "unmatched_files": [os.path.basename(p) for p in unmatched],
        "n_icbroad": sum(s["icbroad"] for s in spectra),
        "redshifts": [s["redshift"] for s in spectra if s["redshift"] is not None],
    }
    return spectra, stats


def load_spectrum(path):
    """Load a .dat spectrum: returns (wave, flux, flux_err) arrays."""
    d = np.loadtxt(path)
    return d[:, 0], d[:, 1], d[:, 2]


def main():
    spectra, stats = build_spectrum_table()
    print(f"n_spectra={stats['n_spectra']}  matched={stats['n_matched']}  "
          f"unmatched={stats['n_unmatched']}  unique_objects={stats['n_unique_objects']}")
    print("broad label dist:", stats["broad_label_dist"])
    print("n_icbroad:", stats["n_icbroad"])
    if stats["unmatched_files"]:
        print("unmatched:", stats["unmatched_files"])
    # per-row table
    out = os.path.join(os.path.dirname(__file__), "..", "results", "spectrum_table.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "obj", "epoch", "atel_type", "broad", "uncertain",
                    "icbroad", "redshift", "phase", "matched"])
        for s in spectra:
            w.writerow([os.path.basename(s["file"]), s["obj"], s["epoch"],
                        s["atel_type"], s["broad"], s["uncertain"], s["icbroad"],
                        s["redshift"], s["phase"], s["matched"]])
    print("wrote", out)
    with open(os.path.join(os.path.dirname(__file__), "..", "results", "data_facts.json"), "w") as f:
        json.dump(stats, f, indent=2, default=float)
    print("wrote data_facts.json")


if __name__ == "__main__":
    main()
