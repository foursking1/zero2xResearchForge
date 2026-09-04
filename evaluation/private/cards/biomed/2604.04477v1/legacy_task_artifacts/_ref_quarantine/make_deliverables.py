"""
Build the required deliverables from my own computed results:
  - results/metrics.json          (machine-readable key metrics + claim verdicts)
  - results/evidence_table.csv    (indicator name / value / definition)
  - results/robustness.json       (multi-seed Dice robustness, computed here)

All numbers come from evaluate_all.py / noise_sensitivity.py outputs in
results/, which in turn are computed from the frozen data (checkpoint +
deterministic synthetic test set). No paper numbers are injected as results;
paper values are kept in a clearly-labelled "paper_values_for_reference" block.

Usage:
    python make_deliverables.py [--results_dir <path>]
"""

import argparse
import csv
import json
import os

import numpy as np
import torch


def compute_multi_seed_robustness(data_root, shape=(16, 32, 32), n_per_seed=20, seeds=(100, 200, 300, 400)):
    """Compute Dice on independent deterministic test-seed blocks (same protocol as evaluate_all)."""
    import sys
    sys.path.insert(0, os.path.join(data_root, "src"))
    from models.mvisfold import build_model
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_all_metrics

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(os.path.join(data_root, "checkpoints", "stage1_best.pth"),
                      map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    out = {"n_per_seed": n_per_seed, "seeds": {}}
    all_dice = []
    with torch.no_grad():
        for s in seeds:
            dices = []
            for k in range(n_per_seed):
                gen = VascularTreeGenerator(shape=shape, max_branches=15, seed=s + k)
                phantom = gen.generate()
                ch = generate_sruse_channels(phantom, noise_level=0.1, seed=s + k + 5000)
                x = torch.from_numpy(ch).unsqueeze(0).float().to(device)
                pred = model(x)[0, 0].cpu().numpy()
                dices.append(compute_all_metrics(pred, phantom.volume)["dice"])
            out["seeds"][str(s)] = {
                "dice_mean": round(float(np.mean(dices)), 6),
                "dice_std": round(float(np.std(dices)), 6),
            }
            all_dice.extend(dices)
    out["all_seeds_pooled"] = {
        "dice_mean": round(float(np.mean(all_dice)), 6),
        "dice_std": round(float(np.std(all_dice)), 6),
        "n": int(len(all_dice)),
    }
    return out


def build_claims(fm):
    t1 = fm["table1"]["MVis-Fold (small, ours)"]
    t2 = fm["table2"]
    iv = fm["internal_validation"]

    c01_sub = {
        "dice>=0.95": bool(t1["dice_mean"] >= 0.95),
        "sens>=0.94": bool(t1["sens_mean"] >= 0.94),
        "spec>=0.95": bool(t1["spec_mean"] >= 0.95),
        "acc>=0.95": bool(t1["acc_mean"] >= 0.95),
    }
    tri_dice = fm["table1"]["TripoSR proxy (Tier 2 heuristic)"]["dice_mean"]
    lrm_dice = fm["table1"]["OpenLRM proxy (Tier 2 heuristic)"]["dice_mean"]
    beats_baselines = bool(t1["dice_mean"] > tri_dice and t1["dice_mean"] > lrm_dice)

    claims = {
        "C01": {
            "claim": "Dice>=0.95, sens>=0.94, spec>=0.95, acc>=0.95 on 3D segmentation, outperform SparseNeuS/OpenLRM/TripoSR",
            "measured": {
                "dice": t1["dice_mean"], "sensitivity": t1["sens_mean"],
                "specificity": t1["spec_mean"], "accuracy": t1["acc_mean"],
                "sub_parts": c01_sub,
                "beats_available_baselines": beats_baselines,
                "TripoSR_proxy_dice": tri_dice, "OpenLRM_proxy_dice": lrm_dice,
            },
            "verdict": "contradicted",
            "reason": ("Frozen synthetic test set (n=50): Dice=0.830<0.95 and sensitivity=0.936<0.94 "
                       "(specificity=0.990>=0.95 and accuracy=0.988>=0.95 pass). The model also does not "
                       "outperform the available TripoSR heuristic proxy (0.920>0.830); it only beats the "
                       "OpenLRM proxy (0.778). Original SparseNeuS/OpenLRM/TripoSR are not in the frozen data."),
        },
        "C02": {
            "claim": "vessel density error<0.02 mm/mm3 and mean diameter error<3 um, >1000x and >50x improvement over 2D SRUS",
            "measured": {
                "vd_error": t2["vd_error_mvis_mean"], "md_error": t2["md_error_mvis_mean"],
                "vd_improvement_ratio": t2["vd_improvement_ratio"],
                "md_improvement_ratio": t2["md_improvement_ratio"],
            },
            "verdict": "contradicted",
            "reason": ("vs synthetic GT: VD error=27.00 mm/mm3 >> 0.02; MD error=4.10 um > 3 um; "
                       "improvement ratios vs the 2D-SRUS proxy are 3.3x (VD) and 0.57x (MD), far below "
                       "1000x/50x. Note the frozen 2D-SRUS reference is an area-fraction with mismatched units, "
                       "so the ratio is only directional, not a faithful reproduction of the paper's 1353x/55x."),
        },
        "C03": {
            "claim": "extracted vessel density Pearson r>=0.85 (p<0.01) vs histopathology gold standard",
            "measured": {
                "pearson_vd_r": t2["pearson_vd_r"], "pearson_vd_p": t2["pearson_vd_p"],
                "pearson_md_r": t2["pearson_md_r"], "pearson_md_p": t2["pearson_md_p"],
            },
            "verdict": "inconclusive",
            "reason": ("The claim is specifically against a histopathology gold standard, which is NOT part of "
                       "the frozen data, so the paper's r=0.892 cannot be reproduced. The closest available test "
                       "(correlation with the synthetic ground truth) gives r=0.132 (p=0.362) for vessel density, "
                       "which would contradict the r>=0.85 threshold if applied to that proxy."),
        },
        "C04": {
            "claim": "internal validation set Dice coefficient >= 0.95",
            "measured": {"internal_val_dice": iv["dice_mean"], "internal_val_dice_std": iv["dice_std"]},
            "verdict": "contradicted",
            "reason": (f"Deterministic internal-validation block (seeds 100..119, max_branches=10): "
                       f"Dice={iv['dice_mean']:.3f} < 0.95. The checkpoint itself records best training "
                       f"validation Dice=0.8261, also < 0.95."),
        },
    }
    return claims


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results_dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--data_root", type=str, default=r"F:/dataset/2604.04477v1")
    args = ap.parse_args()
    rd = os.path.abspath(args.results_dir)

    with open(os.path.join(rd, "full_metrics.json")) as f:
        fm = json.load(f)
    with open(os.path.join(rd, "noise_sensitivity.json")) as f:
        noise = json.load(f)

    claims = build_claims(fm)

    paper_ref = {
        "dice": 0.959, "sensitivity": 0.951, "specificity": 0.957, "accuracy": 0.962,
        "hausdorff95": 3.2, "vd_error": 0.012, "md_error": 2.16,
        "vd_fold_improvement": 1353, "md_fold_improvement": 55,
        "pearson_vd_r": 0.892, "internal_val_dice": 0.964,
    }

    metrics_out = {
        "n_test_samples": fm["n_test_samples"],
        "shape": fm["shape"],
        "max_branches": fm["max_branches"],
        "noise_level": fm["noise_level"],
        "checkpoint": fm["checkpoint"],
        "table1": fm["table1"],
        "table2": fm["table2"],
        "internal_validation": fm["internal_validation"],
        "statistics": fm["statistics"],
        "noise_sensitivity": noise["results"],
        "claims": claims,
        "paper_values_for_reference": paper_ref,
        "label": "SYNTHETIC DATA ONLY -- NOT VALIDATED ON BIOLOGICAL TISSUE",
    }
    with open(os.path.join(rd, "metrics.json"), "w") as f:
        json.dump(metrics_out, f, indent=2)

    # ---- evidence table ----
    rows = []
    def add(claim, metric, value, definition):
        rows.append({"claim_id": claim, "metric": metric, "value": value, "definition": definition})

    for m, v in [("dice_mean", fm["table1"]["MVis-Fold (small, ours)"]),
                 ("sens_mean", None), ("spec_mean", None), ("acc_mean", None),
                 ("hd95_mean", None), ("time_mean", None)]:
        pass
    t1 = fm["table1"]["MVis-Fold (small, ours)"]
    for k in ["dice_mean", "dice_std", "sens_mean", "sens_std", "spec_mean", "spec_std",
              "acc_mean", "acc_std", "hd95_mean", "time_mean"]:
        add("C01", f"MVis-Fold_{k}", t1[k], "Table 1 segmentation metric (mean/std), frozen synthetic test set")
    add("C01", "MVis-Fold_dice_ci95", json.dumps(t1["dice_ci95"]), "bootstrap 95% CI on Dice (2000 resamples)")
    add("C01", "TripoSR proxy (Tier 2 heuristic)_dice_mean",
        fm["table1"]["TripoSR proxy (Tier 2 heuristic)"]["dice_mean"],
        "baseline Dice on the same frozen test set")
    add("C01", "OpenLRM proxy (Tier 2 heuristic)_dice_mean",
        fm["table1"]["OpenLRM proxy (Tier 2 heuristic)"]["dice_mean"],
        "baseline Dice on the same frozen test set")

    t2 = fm["table2"]
    for k in ["vd_error_mvis_mean", "vd_error_srus_mean", "md_error_mvis_mean", "md_error_srus_mean",
              "vd_improvement_ratio", "md_improvement_ratio"]:
        add("C02", k, t2[k], "Table 2 parameter accuracy / correlation (vs synthetic GT)")
    for k in ["pearson_vd_r", "pearson_vd_p", "pearson_md_r", "pearson_md_p"]:
        add("C03", k, t2[k], "Table 2 parameter accuracy / correlation (vs synthetic GT)")
    iv = fm["internal_validation"]
    add("C04", "internal_val_dice_mean", iv["dice_mean"], "Dice on internal validation set (training protocol, deterministic)")
    add("C04", "internal_val_dice_std", iv["dice_std"], "std over internal validation samples")
    add("C04", "checkpoint_best_train_val_dice", fm["checkpoint"]["best_dice_at_save"],
        "best validation Dice stored in frozen checkpoint")
    add("C04", "internal_val_dice_ci95", json.dumps(iv["dice_ci95"]), "bootstrap 95% CI")

    for nl, res in noise["results"].items():
        add("robustness", f"noise_{nl}_dice_mean", res["dice_mean"], "noise sensitivity, frozen test set")
        add("robustness", f"noise_{nl}_sens_mean", res["sens_mean"], "noise sensitivity, frozen test set")

    with open(os.path.join(rd, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["claim_id", "metric", "value", "definition"])
        w.writeheader()
        w.writerows(rows)

    # ---- multi-seed robustness (computed now) ----
    rob = compute_multi_seed_robustness(args.data_root)
    with open(os.path.join(rd, "robustness.json"), "w") as f:
        json.dump(rob, f, indent=2)

    print(f"Wrote metrics.json, evidence_table.csv, robustness.json -> {rd}")
    print(json.dumps({cid: c["verdict"] for cid, c in claims.items()}))


if __name__ == "__main__":
    main()
