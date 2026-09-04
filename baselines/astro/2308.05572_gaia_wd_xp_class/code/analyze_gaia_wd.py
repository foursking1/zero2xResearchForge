# -*- coding: utf-8 -*-
"""
Gaia WD XP spectral classification -- population composition verification.

Task: 2308.05572_gaia_wd_xp_class
Paper anchor: Vincent et al., A&A 682, A5 (2024), arXiv:2308.05572.
  - 100,886 high-confidence WD candidates (PWD>0.9, G<20.5)
  - 89,188 high-confidence classifications / 11,698 uncertain (probability < 0.65)
  - Table 2: DA 77,330 / DB 5,688 / DC 4,082 / DO 215 / DQ 601 / DZ 1,272
  - Teff=-999: paper 1,080 (SS4.2); DA Teff>300,000K: paper 34 (version drift expected)

Fixed-width parse of catalog.dat.gz (338 bytes/row, authoritative byte map in ReadMe).
All metrics recomputed from the frozen data: F:/dataset/astro/2308.05572_gaia_wd_xp_class/
"""
import os
import json
import gzip
import numpy as np
import pandas as pd

DATA = r"F:/dataset/astro/2308.05572_gaia_wd_xp_class"
outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(outdir, exist_ok=True)

# ----------------------------------------------------------------------------
# 1. Fixed-width parse (byte positions from ReadMe; 0-based slicing)
# ----------------------------------------------------------------------------
# field list: (0-based start, 0-based end, name, cast)
FIELDS = [
    (0, 19, "GaiaDR3", "int"),
    (20, 23, "SpType", "str"),
    (24, 33, "umag", "float"),
    (34, 41, "gmag", "float"),
    (42, 49, "rmag", "float"),
    (50, 57, "imag", "float"),
    (58, 67, "zmag", "float"),
    (68, 90, "e_Fluxu", "float"),
    (91, 113, "e_Fluxg", "float"),
    (114, 136, "e_Fluxr", "float"),
    (137, 159, "e_Fluxi", "float"),
    (160, 182, "e_Fluxz", "float"),
    (183, 187, "PDA", "float"),
    (188, 192, "PDB", "float"),
    (193, 197, "PDC", "float"),
    (198, 202, "PDO", "float"),
    (203, 207, "PDQ", "float"),
    (208, 212, "PDZ", "float"),
    (213, 219, "Teff", "float"),
    (220, 228, "logg", "float"),
    (229, 237, "M", "float"),
    (238, 244, "e_Teff", "float"),
    (245, 253, "e_logg", "float"),
    (254, 263, "e_M", "float"),
    (264, 273, "umagcor", "float"),
    (274, 283, "e_umagcor", "float"),
    (284, 311, "comp", "str"),
    (312, 318, "logCHe", "float"),
    (319, 328, "logL", "float"),
    (329, 338, "e_logL", "float"),
]

def parse(f):
    cols = {name: [] for _, _, name, _ in FIELDS}
    for line in f:
        b = line if isinstance(line, bytes) else line.encode()
        if len(b) < 338:
            continue
        for s, e, name, cast in FIELDS:
            raw = b[s:e].decode().strip()
            if cast == "int":
                cols[name].append(int(raw) if raw else 0)
            elif cast == "float":
                cols[name].append(float(raw) if raw else np.nan)
            else:
                cols[name].append(raw)
    out = {}
    for name, vals in cols.items():
        if FIELDS[[f[2] for f in FIELDS].index(name)][3] == "str":
            out[name] = np.array(vals, dtype=object)
        elif FIELDS[[f[2] for f in FIELDS].index(name)][3] == "int":
            out[name] = np.array(vals, dtype=np.int64)
        else:
            out[name] = np.array(vals, dtype=float)
    return out

with gzip.open(os.path.join(DATA, "catalog.dat.gz"), "rb") as f:
    d = parse(f)

n = len(d["GaiaDR3"])
CLASSES = ["DA", "DB", "DC", "DO", "DQ", "DZ"]
PROB_COLS = ["PDA", "PDB", "PDC", "PDO", "PDQ", "PDZ"]
probs = np.column_stack([d[c] for c in PROB_COLS])

sptype = d["SpType"]
teff = d["Teff"]

# ----------------------------------------------------------------------------
# 2. SpType-based counts (colon suffix = uncertain)
# ----------------------------------------------------------------------------
high_conf = np.array([not s.endswith(":") for s in sptype])
base_type = np.array([s.rstrip(":") for s in sptype])
uncertain = ~high_conf

counts_hc = {c: int(np.sum((base_type == c) & high_conf)) for c in CLASSES}
counts_unc = {c: int(np.sum((base_type == c) & uncertain)) for c in CLASSES}
counts_argmax = {}
for ci, c in enumerate(CLASSES):
    counts_argmax[c] = int(np.sum(np.argmax(probs, axis=1) == ci))
n_hc_total = int(high_conf.sum())
n_unc_total = int(uncertain.sum())
n_maxge65 = int(np.sum(np.max(probs, axis=1) >= 0.65))

# ----------------------------------------------------------------------------
# 3. Physical parameters
# ----------------------------------------------------------------------------
n_teff_missing = int(np.sum(teff == -999.0))
da_mask = (base_type == "DA") & high_conf
n_da_hot = int(np.sum(da_mask & (teff > 300000.0)))
n_da_hot_all = int(np.sum((base_type == "DA") & (teff > 300000.0)))

# ----------------------------------------------------------------------------
# 4. Fraction stats
# ----------------------------------------------------------------------------
da_frac = counts_hc["DA"] / n
hc_frac = n_hc_total / n

# ----------------------------------------------------------------------------
# 5. Outputs
# ----------------------------------------------------------------------------
metrics = {
    "total_rows": n,
    "unique_gaia": int(np.unique(d["GaiaDR3"]).size),
    "sp_type_counts_high_conf": counts_hc,
    "sp_type_counts_uncertain": counts_unc,
    "n_high_conf_total": n_hc_total,
    "n_uncertain_total": n_unc_total,
    "n_argmax_total": int(np.sum(list(counts_argmax.values()))),
    "argmax_counts": counts_argmax,
    "n_max_prob_ge_065": n_maxge65,
    "da_fraction": float(da_frac),
    "high_conf_fraction": float(hc_frac),
    "n_teff_neg999": n_teff_missing,
    "n_da_teff_gt_300000_highconf": n_da_hot,
    "n_da_teff_gt_300000_all": n_da_hot_all,
    "paper_anchor": {
        "paper_total": 100886,
        "paper_high_conf": 89188,
        "paper_uncertain": 11698,
        "paper_da": 77330, "paper_db": 5688, "paper_dc": 4082,
        "paper_do": 215, "paper_dq": 601, "paper_dz": 1272,
        "paper_da_frac": 0.7665,
        "paper_teff_neg999": 1080,
        "paper_da_teff_gt_300000": 34,
    },
}

rows = []
rows.append({"class": "ALL", "n_high_conf": n_hc_total, "n_uncertain": n_unc_total,
             "n_argmax": int(np.sum(list(counts_argmax.values()))),
             "frac_high_conf": float(hc_frac)})
for c in CLASSES:
    rows.append({"class": c, "n_high_conf": counts_hc[c], "n_uncertain": counts_unc[c],
                 "n_argmax": counts_argmax[c],
                 "frac_high_conf": float(counts_hc[c] / n)})
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(outdir, "evidence_table.csv"), index=False)
with open(os.path.join(outdir, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

# ----------------------------------------------------------------------------
# 6. Figure: class counts (high-conf vs uncertain vs argmax)
# ----------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(CLASSES))
w = 0.28
hc = [counts_hc[c] for c in CLASSES]
unc = [counts_unc[c] for c in CLASSES]
am = [counts_argmax[c] for c in CLASSES]
ax.bar(x - w, hc, w, label="high-confidence (SpType no colon)", color="steelblue")
ax.bar(x, unc, w, label="uncertain (colon)", color="orange")
ax.bar(x + w, am, w, label="argmax(PDA..PDZ)", color="gray", alpha=0.6)
ax.set_xticks(x)
ax.set_xticklabels(CLASSES)
ax.set_ylabel("N objects")
ax.set_title("Gaia WD XP classification counts (N=100,886)")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(outdir, "figure.svg"))
fig.savefig(os.path.join(outdir, "figure.png"), dpi=150)

print(json.dumps(metrics, indent=2))
