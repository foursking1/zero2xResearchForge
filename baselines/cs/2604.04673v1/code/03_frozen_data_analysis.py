"""
Analyze the FROZEN output data shipped with the reproduction workspace
(F:/dataset/2604.04673v1/output/data/*.json).

Computes the claim-relevant metrics from the frozen data itself:
  - MLE risk vs minimax level p  (claims C01-C04 reference minimax level)
  - BetaPrime max risk vs p
  - Fixed-scale BNN risk vs p at large ||theta||
  - Dropout risk ordering
  - Horseshoe sparsity dependence at p=5
"""
import json
import glob
from pathlib import Path

import numpy as np

DATA_DIR = Path(r"F:\dataset\2604.04673v1\output\data")


def load_latest(pattern, p=None):
    files = sorted(glob.glob(str(DATA_DIR / pattern)))
    out = None
    for f in files:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if p is None or d.get("p") == p:
            out = d
    return out


def summarize():
    report = {}

    # --- Radial p=5 : use the longest run (r up to 200) ---
    d5 = load_latest("*radial_p5*.json", 5)
    # pick run with max r coverage
    best5 = None
    for f in sorted(glob.glob(str(DATA_DIR / "*radial_p5*.json"))):
        d = json.load(open(f))
        if best5 is None or len(d["r_values"]) > len(best5["r_values"]):
            best5 = d
    report["radial_p5"] = _summarize_radial(best5)

    d50 = load_latest("*radial_p50*.json", 50)
    report["radial_p50"] = _summarize_radial(d50)

    d100 = load_latest("*radial_p100*.json", 100)
    report["radial_p100"] = _summarize_radial(d100)

    # --- Sparsity p=5 ---
    sp = load_latest("*sparsity_p5_zz_hs*.json", 5)
    sp2 = load_latest("*sparsity_p5_fixed_hs_v2*.json", 5)
    report["sparsity_p5_zz"] = _summarize_sparsity(sp)
    report["sparsity_p5_v2"] = _summarize_sparsity(sp2)

    return report


def _summarize_radial(d):
    if d is None:
        return {"missing": True}
    r = np.array(d["r_values"])
    out = {"p": d["p"], "r_min": float(r.min()), "r_max": float(r.max())}
    for k in ["fixed_risk", "betaprime_risk", "dropout_risk"]:
        arr = np.array(d[k])
        p = d["p"]
        out[f"{k}_min"] = float(arr.min())
        out[f"{k}_max"] = float(arr.max())
        out[f"{k}_at_max_r"] = float(arr[-1])
        exceed = arr > p
        out[f"{k}_n_exceed_p"] = int(exceed.sum())
        out[f"{k}_first_exceed_r"] = (
            float(r[np.argmax(exceed)]) if exceed.any() else None
        )
    # ordering: dropout between betaprime and fixed
    fx = np.array(d["fixed_risk"])
    bp = np.array(d["betaprime_risk"])
    dp = np.array(d["dropout_risk"])
    n = len(fx)
    between = sum(1 for i in range(n) if min(bp[i], fx[i]) <= dp[i] <= max(bp[i], fx[i]))
    out["dropout_between_pct"] = between / n * 100
    # ordering fixed >= dropout >= betaprime
    ordered = sum(1 for i in range(n) if fx[i] >= dp[i] >= bp[i])
    out["fixed_ge_dropout_ge_betaprime_pct"] = ordered / n * 100
    return out


def _summarize_sparsity(d):
    if d is None:
        return {"missing": True}
    r = np.array(d["r_values"])
    out = {"p": d["p"], "r_values": r.tolist()}
    bp = np.array(d["betaprime_risk"])
    out["betaprime_min"] = float(bp.min())
    out["betaprime_max"] = float(bp.max())
    out["betaprime_at_max_r"] = float(bp[-1])
    hs = d.get("horseshoe_risk", {})
    for k, arr in sorted(hs.items(), key=lambda x: int(x[0])):
        a = np.array(arr)
        out[f"hs_k{k}_min"] = float(a.min())
        out[f"hs_k{k}_max"] = float(a.max())
        out[f"hs_k{k}_at_max_r"] = float(a[-1])
        # fraction of points where hs(k) < betaprime
        n = min(len(a), len(bp))
        frac = sum(1 for i in range(n) if a[i] < bp[i]) / n * 100
        out[f"hs_k{k}_below_betaprime_pct"] = frac
    return out


if __name__ == "__main__":
    rep = summarize()
    out = Path(__file__).resolve().parent.parent / "results"
    out.mkdir(parents=True, exist_ok=True)
    json.dump(rep, open(out / "frozen_data_summary.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))
