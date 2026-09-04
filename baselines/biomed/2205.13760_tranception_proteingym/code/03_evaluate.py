"""Evaluate zero-shot scores against frozen DMS scores.

For every assay x method pair:
  - drop variants whose non-single/multi count or NaN score -> keep all scored,
  - Spearman rho between model score and DMS_score (scipy),
  - write results/evidence_table.csv and results/metrics.json,
  - produce summary prints and figures.

Primary numbers use the `tables` LM scores; GFP `joint` masked-marginal is
reported separately as a fidelity check.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ASSAYS, ROOT, get_meta, load_reference

SCORES_DIR = os.path.join(ROOT, "results")

LM_METHODS = {
    "LME-2 650M": ("lm_scores", "tables", "esm2_t33_650M"),
    "LME-2 8M": ("lm_scores", "tables", "esm2_t6_8M"),
    "LME-2 650M jointGFP": ("lm_scores", "joint", "esm2_t33_650M"),
}

BASELINES = [
    "baseline_blosum62",
    "baseline_blosum62_norm",
    "baseline_null",
]

METHOD_LABELS = {
    "LM_esm2_650M": "ESM-2 650M (masked-marginal)",
    "LM_esm2_8M": "ESM-2 8M (masked-marginal)",
    "LM_esm2_650M_joint": "ESM-2 650M joint masked-marginal",
    "baseline_blosum62": "BLOSUM62 site-independent",
    "baseline_blosum62_norm": "BLOSUM62 per-position z-score",
    "baseline_null": "null (uniform noise)",
}

# which joint LM entry to use per assay (joint is only meaningful for GFP,
# which has multi-mutants; identical to tables for single-mutant assays)
JOINT_ASSAY = "GFP_AEQVI_Sarkisyan_2016"


def load_scores(fid, method):
    if method.startswith("LM_"):
        mode = "tables"
        model = "esm2_t33_650M" if "650M" in method else "esm2_t6_8M"
        if "joint" in method:
            mode = "joint"
        path = os.path.join(SCORES_DIR, "lm_scores", mode, model, f"{fid}.csv")
        assert os.path.exists(path), path
        return pd.read_csv(path)[["mutant", "DMS_score", "score"]]
    path = os.path.join(SCORES_DIR, "baseline_scores", f"{method}__{fid}.csv")
    return pd.read_csv(path)[["mutant", "DMS_score", "score"]]


def within_position_mean_rho(fid, df):
    """Mean within-position Spearman rho over positions with >=5 single mutants
    (the per-position resolution of single-mutant prediction)."""
    from scipy.stats import spearmanr
    df = df.copy()
    df["nmut"] = df["mutant"].str.count(":") + 1
    sing = df[df["nmut"] == 1].copy()
    sing["pos1"] = sing["mutant"].str.extract(r"[A-Z](\d+)").astype(int)
    rs = []
    for _, g in sing.groupby("pos1"):
        if len(g) >= 5:
            r, _ = spearmanr(g["score"], g["DMS_score"])
            if np.isfinite(r):
                rs.append(r)
    return round(float(np.mean(rs)), 4) if rs else None


def main():
    ref = load_reference()
    user_methods = sys.argv[1:] if len(sys.argv) > 1 else None

    lm_keys = ["LM_esm2_650M", "LM_esm2_8M", "LM_esm2_650M_joint"]

    rows = []
    results = {}
    for fid in ASSAYS:
        meta = get_meta(ref, fid)
        assay_rows = []
        all_methods = lm_keys + BASELINES
        for method in all_methods:
            if user_methods and method not in user_methods:
                continue
            if "joint" in method and fid != JOINT_ASSAY:
                continue
            df = load_scores(fid, method).dropna(subset=["score"])
            rho, p = spearmanr(df["score"], df["DMS_score"])
            rows.append({
                "assay": fid,
                "uniprot_id": meta["uniprot_id"],
                "method": method,
                "method_label": METHOD_LABELS[method],
                "spearman_rho": round(float(rho), 4),
                "spearman_p": float(p),
                "n_variants": int(len(df)),
            })
            assay_rows.append((method, float(rho)))
        results[fid] = {"meta": meta, "rho": dict(assay_rows)}

    ev = pd.DataFrame(rows)
    ev_path = os.path.join(SCORES_DIR, "evidence_table.csv")
    ev[["assay", "uniprot_id", "method", "spearman_rho", "n_variants"]].to_csv(ev_path, index=False)
    print(ev.to_string(index=False))

    # ---- aggregate summaries ----
    agg = {}
    for method in ev["method"].unique():
        sub = ev[ev["method"] == method]
        agg[method] = {
            "mean_rho": round(float(sub["spearman_rho"].mean()), 4),
            "median_rho": round(float(sub["spearman_rho"].median()), 4),
            "n_assays": int(len(sub)),
        }
        print(f"{method:26s} mean rho={sub['spearman_rho'].mean():.4f} "
              f"median={sub['spearman_rho'].median():.4f} "
              f"almost-min... per-assay: {[round(x,3) for x in sub['spearman_rho']]}")

    # primary comparison: pooled 650M tables vs BLOSUM62 tables
    rho_lm = {fid: results[fid]["rho"]["LM_esm2_650M"] for fid in ASSAYS}
    rho_lm8 = {fid: results[fid]["rho"]["LM_esm2_8M"] for fid in ASSAYS}
    rho_bl = {fid: results[fid]["rho"]["baseline_blosum62"] for fid in ASSAYS}
    rho_bln = {fid: results[fid]["rho"]["baseline_blosum62_norm"] for fid in ASSAYS}
    rho_join = {JOINT_ASSAY: results[JOINT_ASSAY]["rho"]["LM_esm2_650M_joint"]}

    win_650 = sum(1 for f in ASSAYS if rho_lm[f] > rho_bl[f])
    win_650_8 = sum(1 for f in ASSAYS if rho_lm8[f] > rho_bl[f])
    print(f"\nESM-2 650M beats BLOSUM62 in {win_650}/{len(ASSAYS)} assays (mean "
          f"{np.mean(list(rho_lm.values())):.4f} vs {np.mean(list(rho_bl.values())):.4f})")
    print(f"ESM-2 8M beats BLOSUM62 in {win_650_8}/{len(ASSAYS)} assays (mean "
          f"{np.mean(list(rho_lm8.values())):.4f} vs {np.mean(list(rho_bl.values())):.4f})")
    print(f"GFP joint vs tables rho: {rho_join[JOINT_ASSAY]:.4f} vs {rho_lm['GFP_AEQVI_Sarkisyan_2016']:.4f}")

    # MSA-depth stratification (paper anchor 3: shallow = low Neff -> LM gain)
    neff_bins = []
    for fid in ASSAYS:
        neff = results[fid]["meta"]["MSA_Neff"]
        cat = results[fid]["meta"]["MSA_Neff_L_category"]
        neff_bins.append((fid, neff, cat, rho_lm[fid], rho_bl[fid]))

    # conclusion label
    frac = win_650 / len(ASSAYS)
    delta_mean = np.mean(list(rho_lm.values())) - np.mean(list(rho_bl.values()))
    if frac >= 0.6 and delta_mean > 0:
        label = "supported"
    elif frac >= 0.4 and delta_mean > 0:
        label = "partially_supported"
    elif delta_mean <= 0:
        label = "contradicted"
    else:
        label = "inconclusive"
    print(f"\nCONCLUSION: {label}  (LM wins {win_650}/{len(ASSAYS)}, Δmean_rho={delta_mean:+.4f})")

    metrics = {
        "task_id": "2205.13760_tranception_proteingym",
        "conclusion": label,
        "conclusion_tiers": "supported / partially_supported / contradicted / inconclusive",
        "paper_claim": ("Protein language models predict variant effects in zero-shot "
                        "fashion; LM/masked-LM zero-shot Spearman rho >= simple "
                        "site-independent baseline across most DMS assays"),
        "n_assays": len(ASSAYS),
        "per_assay": {},
    }
    for fid in ASSAYS:
        nmut = load_scores(fid, "LM_esm2_650M")["mutant"].str.count(":") + 1
        wpr = within_position_mean_rho(fid, load_scores(fid, "LM_esm2_650M"))
        nvar = int(results[fid]["rho"] and next(
            r["n_variants"] for r in rows if r["assay"] == fid and r["method"] == "LM_esm2_650M"))
        metrics["per_assay"][fid] = {
            "seq_len": int(ref[ref.DMS_id == fid].iloc[0]["seq_len"]),
            "n_variants": nvar,
            "n_single_mutants": int((nmut == 1).sum()),
            "n_multi_mutants": int((nmut > 1).sum()),
            "within_position_mean_rho_singles": wpr,
            "rho_lm_650M": rho_lm[fid], "rho_lm_8M": rho_lm8[fid],
            "rho_baseline_blosum62": rho_bl[fid],
            "MSA_Neff": results[fid]["meta"]["MSA_Neff"],
            "MSA_Neff_L_category": results[fid]["meta"]["MSA_Neff_L_category"],
            "taxon": results[fid]["meta"]["taxon"],
        }

    metrics["method_aggregates"] = agg
    metrics["main_comparison"] = {
        "LM_tables": "LM_esm2_650M", "baseline": "baseline_blosum62",
        "n_wins": win_650, "n_ties_or_losses": len(ASSAYS) - win_650,
        "mean_rho_lm": round(float(np.mean(list(rho_lm.values()))), 4),
        "mean_rho_baseline": round(float(np.mean(list(rho_bl.values()))), 4),
        "mean_delta": round(delta_mean, 4),
    }
    metrics["gfp_joint_vs_tables"] = {
        "joint_rho": rho_join[JOINT_ASSAY],
        "tables_rho": rho_lm[JOINT_ASSAY],
    }
    metrics["msa_depth_stratification"] = [
        {"assay": f, "MSA_Neff": n, "category": cat, "rho_lm": rl, "rho_baseline": rb}
        for f, n, cat, rl, rb in neff_bins
    ]
    with open(os.path.join(SCORES_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nwrote", ev_path, "and", os.path.join(SCORES_DIR, "metrics.json"))


if __name__ == "__main__":
    main()