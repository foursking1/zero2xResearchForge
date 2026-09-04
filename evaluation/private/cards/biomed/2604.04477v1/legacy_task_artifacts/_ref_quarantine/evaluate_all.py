"""
Full evaluation for MVis-Fold claims (C01-C04) on the frozen reproduction workspace.

Data root (frozen, read in place):  F:/dataset/2604.04477v1
  - checkpoints/stage1_best.pth  (trained MVis-Fold small model, stage=1_diverse)
  - src/                          (reference reproduction source: model/data/eval)

What this script does (all numbers are actually computed, not taken from the paper):
  1. Load the frozen MVis-Fold checkpoint.
  2. Deterministically regenerate the synthetic test set (n=50, seeds 300..349,
     max_branches=15, noise=0.1, shape 16x32x32) -- same protocol as the reference
     run_full_eval.py.
  3. Table 1: Dice / Sensitivity / Specificity / Accuracy / HD95 for MVis-Fold and for
     the available frozen baseline proxies (TripoSR, OpenLRM heuristic wrappers).
  4. Table 2: vessel-density & mean-diameter errors vs synthetic ground truth for
     MVis-Fold (3D) and 2D SRUS direct measurement; improvement ratios; Pearson r.
  5. Internal validation: Dice on seeds 100..119 / max_branches=10 (matches the training
     validation protocol used for the frozen checkpoint).
  6. Statistical tests (Shapiro-Wilk on Dice, Wilcoxon signed-rank for VD error, Cohen's d).
  7. Writes agent_solution/results/*.json|csv and prints a summary.

Usage:
    python evaluate_all.py [--n_test 50] [--data_root F:/dataset/2604.04477v1] [--out_dir <path>]
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import torch
from scipy import stats as scipy_stats

# ------------------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------------------
DEFAULT_DATA_ROOT = r"F:/dataset/2604.04477v1"


def resolve_paths(data_root: str):
    """Return (root, src_dir, checkpoint_path) after basic sanity checks."""
    root = os.path.abspath(data_root)
    src_dir = os.path.join(root, "src")
    ckpt_path = os.path.join(root, "checkpoints", "stage1_best.pth")
    for p in (root, src_dir, ckpt_path):
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing frozen path: {p}")
    return root, src_dir, ckpt_path


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_test", type=int, default=50, help="number of frozen test samples")
    ap.add_argument("--data_root", type=str, default=DEFAULT_DATA_ROOT)
    ap.add_argument("--out_dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--shape", type=int, nargs=3, default=[16, 32, 32])
    ap.add_argument("--seed_base", type=int, default=300)
    args = ap.parse_args()

    root, src_dir, ckpt_path = resolve_paths(args.data_root)
    sys.path.insert(0, src_dir)

    from models.mvisfold import build_model
    from baselines.sparseneus_wrapper import TripoSRWrapper, OpenLRMWrapper
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_all_metrics
    from evaluate.vessel_analysis import compare_parameters

    os.makedirs(args.out_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    SHAPE = tuple(args.shape)
    N_TEST = args.n_test
    SEED = args.seed_base
    rng_global = np.random.RandomState(0)

    print(f"data_root   : {root}")
    print(f"device      : {device}")
    print(f"n_test      : {N_TEST}, shape={SHAPE}, max_branches=15, noise=0.1")

    # --------------------------------------------------------------------------
    # 1. Load frozen checkpoint
    # --------------------------------------------------------------------------
    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    ckpt_meta = {
        "stage": ckpt.get("stage"),
        "epoch": ckpt.get("epoch"),
        "best_dice_at_save": ckpt.get("best_dice"),
        "shape": ckpt.get("shape"),
    }
    print(f"Loaded checkpoint: {ckpt_meta}")

    # Baseline proxies (frozen code)
    triposr = TripoSRWrapper()
    openlrm = OpenLRMWrapper()

    # --------------------------------------------------------------------------
    # Test-set generation (deterministic, identical protocol to reference eval)
    # --------------------------------------------------------------------------
    def make_test_sample(idx):
        gen = VascularTreeGenerator(shape=SHAPE, max_branches=15, seed=SEED + idx)
        phantom = gen.generate()
        channels = generate_sruse_channels(phantom, noise_level=0.1, seed=SEED + idx + 5000)
        x = torch.from_numpy(channels).unsqueeze(0).float().to(device)
        return x, phantom

    models_to_eval = {
        "MVis-Fold (small, ours)": lambda x: model(x),
        "TripoSR proxy (Tier 2 heuristic)": lambda x: triposr(x),
        "OpenLRM proxy (Tier 2 heuristic)": lambda x: openlrm(x),
    }

    # --------------------------------------------------------------------------
    # Table 1: segmentation metrics
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TABLE 1: SEGMENTATION PERFORMANCE ON FROZEN SYNTHETIC TEST SET")
    print("=" * 70)

    all_results = {}
    per_sample = {}

    for name, fn in models_to_eval.items():
        metrics = {"dice": [], "sensitivity": [], "specificity": [],
                   "accuracy": [], "hausdorff_95": [], "time": []}
        with torch.no_grad():
            for i in range(N_TEST):
                x, phantom = make_test_sample(i)
                t0 = time.time()
                output = fn(x)
                metrics["time"].append(time.time() - t0)
                pred = output[0, 0].cpu().numpy()
                m = compute_all_metrics(pred, phantom.volume)
                for k, v in m.items():
                    metrics[k].append(v)

        arr = {k: np.asarray(v) for k, v in metrics.items()}
        # 95% bootstrap CI on Dice
        boot = []
        for _ in range(2000):
            idx = rng_global.randint(0, N_TEST, size=N_TEST)
            boot.append(arr["dice"][idx].mean())
        boot = np.sort(boot)

        result = {
            "dice_mean": round(float(arr["dice"].mean()), 4),
            "dice_std": round(float(arr["dice"].std()), 4),
            "sens_mean": round(float(arr["sensitivity"].mean()), 4),
            "sens_std": round(float(arr["sensitivity"].std()), 4),
            "spec_mean": round(float(arr["specificity"].mean()), 4),
            "spec_std": round(float(arr["specificity"].std()), 4),
            "acc_mean": round(float(arr["accuracy"].mean()), 4),
            "acc_std": round(float(arr["accuracy"].std()), 4),
            "hd95_mean": round(float(arr["hausdorff_95"].mean()), 4),
            "hd95_std": round(float(arr["hausdorff_95"].std()), 4),
            "time_mean": round(float(arr["time"].mean()), 4),
            "time_std": round(float(arr["time"].std()), 4),
            "dice_ci95": [round(float(boot[50]), 4), round(float(boot[1950]), 4)],
            "dice_per_sample": [round(float(v), 4) for v in metrics["dice"]],
        }
        all_results[name] = result
        per_sample[name] = {"dice": metrics["dice"], "sens": metrics["sensitivity"],
                            "spec": metrics["specificity"], "acc": metrics["accuracy"]}
        print(f"  {name}:")
        print(f"    Dice={result['dice_mean']:.4f}+/-{result['dice_std']:.4f} "
              f"(95%CI {result['dice_ci95']})  Sens={result['sens_mean']:.4f} "
              f"Spec={result['spec_mean']:.4f} Acc={result['acc_mean']:.4f} "
              f"HD95={result['hd95_mean']:.2f}  time={result['time_mean']:.4f}s")

    # --------------------------------------------------------------------------
    # Table 2: parameter accuracy vs synthetic GT (mm/mm3 and um)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("TABLE 2: PARAMETER ACCURACY vs SYNTHETIC GROUND TRUTH")
    print("=" * 70)

    vd_errors_mvis, vd_errors_srus = [], []
    md_errors_mvis, md_errors_srus = [], []
    corr_vd = {"mvis": [], "srus": [], "gt": []}
    corr_md = {"mvis": [], "srus": [], "gt": []}
    param_rows = []

    with torch.no_grad():
        for i in range(N_TEST):
            x, phantom = make_test_sample(i)
            out = model(x)[0, 0].cpu().numpy()
            pred_3d = (out > 0.5).astype(np.float64)

            res = compare_parameters(
                prediction_3d=pred_3d,
                channels_2d=x[0].cpu().numpy(),
                ground_truth_density=phantom.vessel_density,
                ground_truth_diameter=phantom.mean_diameter,
                voxel_size_um=10.0,
            )
            vd_errors_mvis.append(res["vd_error_3d"])
            vd_errors_srus.append(res["vd_error_2d"])
            md_errors_mvis.append(res["md_error_3d"])
            md_errors_srus.append(res["md_error_2d"])
            corr_vd["mvis"].append(res["vessel_density_3d"])
            corr_vd["srus"].append(res["vessel_density_2d"])
            corr_vd["gt"].append(phantom.vessel_density)
            corr_md["mvis"].append(res["mean_diameter_3d"])
            corr_md["srus"].append(res["mean_diameter_2d"])
            corr_md["gt"].append(phantom.mean_diameter)
            param_rows.append({
                "sample": i, "gt_vd": phantom.vessel_density, "mvis_vd": res["vessel_density_3d"],
                "srus_vd": res["vessel_density_2d"], "vd_err_mvis": res["vd_error_3d"],
                "vd_err_srus": res["vd_error_2d"], "gt_md": phantom.mean_diameter,
                "mvis_md": res["mean_diameter_3d"], "srus_md": res["mean_diameter_2d"],
                "md_err_mvis": res["md_error_3d"], "md_err_srus": res["md_error_2d"],
            })

    vd_m = np.array(vd_errors_mvis); vd_s = np.array(vd_errors_srus)
    md_m = np.array(md_errors_mvis); md_s = np.array(md_errors_srus)

    vd_imp = float(vd_s.mean() / (vd_m.mean() + 1e-10))
    md_imp = float(md_s.mean() / (md_m.mean() + 1e-10))

    r_vd, p_vd = scipy_stats.pearsonr(corr_vd["mvis"], corr_vd["gt"])
    r_md, p_md = scipy_stats.pearsonr(corr_md["mvis"], corr_md["gt"])
    r_vd_s, p_vd_s = scipy_stats.pearsonr(corr_vd["srus"], corr_vd["gt"])
    r_md_s, p_md_s = scipy_stats.pearsonr(corr_md["srus"], corr_md["gt"])

    table2 = {
        "vd_error_mvis_mean": round(float(vd_m.mean()), 4),
        "vd_error_mvis_std": round(float(vd_m.std()), 4),
        "vd_error_srus_mean": round(float(vd_s.mean()), 4),
        "vd_error_srus_std": round(float(vd_s.std()), 4),
        "md_error_mvis_mean": round(float(md_m.mean()), 4),
        "md_error_mvis_std": round(float(md_m.std()), 4),
        "md_error_srus_mean": round(float(md_s.mean()), 4),
        "md_error_srus_std": round(float(md_s.std()), 4),
        "vd_improvement_ratio": round(vd_imp, 4),
        "md_improvement_ratio": round(md_imp, 4),
        "pearson_vd_r": round(float(r_vd), 4),
        "pearson_vd_p": float(p_vd),
        "pearson_md_r": round(float(r_md), 4),
        "pearson_md_p": float(p_md),
        "pearson_vd_srus_r": round(float(r_vd_s), 4),
        "pearson_vd_srus_p": float(p_vd_s),
        "pearson_md_srus_r": round(float(r_md_s), 4),
        "pearson_md_srus_p": float(p_md_s),
        "gt_vd_mean": round(float(np.mean(corr_vd["gt"])), 4),
        "gt_vd_std": round(float(np.std(corr_vd["gt"])), 4),
        "gt_md_mean": round(float(np.mean(corr_md["gt"])), 4),
        "gt_md_std": round(float(np.std(corr_md["gt"])), 4),
    }

    print(f"  {'Method':<22}{'VD error (mm/mm3)':>22}{'MD error (um)':>18}")
    print(f"  {'2D SRUS (direct)':<22}{table2['vd_error_srus_mean']:>22}{table2['md_error_srus_mean']:>18}")
    print(f"  {'MVis-Fold (3D)':<22}{table2['vd_error_mvis_mean']:>22}{table2['md_error_mvis_mean']:>18}")
    print(f"  VD improvement ratio (SRUS/MVis): {vd_imp:.2f}x")
    print(f"  MD improvement ratio (SRUS/MVis): {md_imp:.2f}x")
    print(f"  Pearson r (VD):  r={r_vd:.4f} (p={p_vd:.2e})")
    print(f"  Pearson r (MD):  r={r_md:.4f} (p={p_md:.2e})")

    # --------------------------------------------------------------------------
    # Internal validation (training protocol: max_branches=10, seeds 100..119)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("INTERNAL VALIDATION (training-protocol seeds 100..119, max_branches=10)")
    print("=" * 70)
    val_dices = []
    with torch.no_grad():
        for k in range(20):
            gen = VascularTreeGenerator(shape=SHAPE, max_branches=10, seed=100 + k)
            phantom = gen.generate()
            ch = generate_sruse_channels(phantom, noise_level=0.1, seed=100 + k + 5000)
            x = torch.from_numpy(ch).unsqueeze(0).float().to(device)
            out = model(x)[0, 0].cpu().numpy()
            m = compute_all_metrics(out, phantom.volume)
            val_dices.append(m["dice"])
    val_dices = np.array(val_dices)
    boot_v = np.sort([val_dices[rng_global.randint(0, 20, 20)].mean() for _ in range(2000)])
    internal_val = {
        "n_samples": int(len(val_dices)),
        "dice_mean": round(float(val_dices.mean()), 4),
        "dice_std": round(float(val_dices.std()), 4),
        "dice_ci95": [round(float(boot_v[50]), 4), round(float(boot_v[1950]), 4)],
    }
    print(f"  Internal validation Dice = {internal_val['dice_mean']:.4f} +/- {internal_val['dice_std']:.4f} "
          f"(95%CI {internal_val['dice_ci95']})")

    # --------------------------------------------------------------------------
    # Statistical tests
    # --------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STATISTICAL TESTS (frozen synthetic test set)")
    print("=" * 70)
    mvis_dice = np.array(per_sample["MVis-Fold (small, ours)"]["dice"])
    w, p_norm = scipy_stats.shapiro(mvis_dice)
    print(f"  Shapiro-Wilk on MVis-Fold Dice: W={w:.4f}, p={p_norm:.4f} "
          f"({'normal' if p_norm > 0.05 else 'non-normal'})")
    # VD error: MVis vs 2D SRUS (paired)
    stat_vd, p_vd_wil = scipy_stats.wilcoxon(vd_m, vd_s)
    diff_vd = vd_m - vd_s
    cohens_d_vd = float(np.mean(diff_vd) / (np.std(diff_vd) + 1e-10))
    print(f"  Wilcoxon signed-rank (VD error MVis vs SRUS): stat={stat_vd:.1f}, p={p_vd_wil:.2e}")
    print(f"  Cohen's d (VD error, MVis - SRUS): {cohens_d_vd:.3f}")
    # MVis-Fold vs best baseline (TripoSR proxy) Dice
    tri_dice = np.array(per_sample["TripoSR proxy (Tier 2 heuristic)"]["dice"])
    w_tri, p_tri = scipy_stats.wilcoxon(mvis_dice, tri_dice)
    print(f"  Wilcoxon (Dice MVis vs TripoSR proxy): stat={w_tri:.1f}, p={p_tri:.2e} "
          f"(mean diff {np.mean(mvis_dice - tri_dice):+.4f})")

    stats_block = {
        "shapiro_w": round(float(w), 4), "shapiro_p": float(p_norm),
        "wilcoxon_vd_stat": float(stat_vd), "wilcoxon_vd_p": float(p_vd_wil),
        "cohens_d_vd": round(cohens_d_vd, 4),
        "wilcoxon_dice_mvis_vs_triposr_stat": float(w_tri),
        "wilcoxon_dice_mvis_vs_triposr_p": float(p_tri),
        "mean_dice_diff_mvis_minus_triposr": round(float(np.mean(mvis_dice - tri_dice)), 4),
        "label": "SYNTHETIC DATA ONLY -- NOT VALIDATED ON BIOLOGICAL TISSUE",
    }

    # --------------------------------------------------------------------------
    # Save outputs
    # --------------------------------------------------------------------------
    out = {
        "n_test_samples": N_TEST,
        "shape": list(SHAPE),
        "max_branches": 15,
        "noise_level": 0.1,
        "checkpoint": ckpt_meta,
        "table1": {k: {kk: vv for kk, vv in v.items() if kk != "dice_per_sample"} for k, v in all_results.items()},
        "table2": table2,
        "internal_validation": internal_val,
        "statistics": stats_block,
    }
    with open(os.path.join(args.out_dir, "table1_segmentation.json"), "w") as f:
        json.dump(out["table1"], f, indent=2)
    with open(os.path.join(args.out_dir, "table2_parameters.json"), "w") as f:
        json.dump({"table2": table2,
                   "vd_errors_mvis": [round(float(v), 4) for v in vd_errors_mvis],
                   "vd_errors_srus": [round(float(v), 4) for v in vd_errors_srus],
                   "md_errors_mvis": [round(float(v), 4) for v in md_errors_mvis],
                   "md_errors_srus": [round(float(v), 4) for v in md_errors_srus]}, f, indent=2)
    with open(os.path.join(args.out_dir, "internal_validation.json"), "w") as f:
        json.dump(internal_val, f, indent=2)

    # per-sample parameters CSV
    import csv
    with open(os.path.join(args.out_dir, "per_sample_parameters.csv"), "w", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(param_rows[0].keys()))
        wcsv.writeheader()
        wcsv.writerows(param_rows)
    # per-sample segmentation CSV
    with open(os.path.join(args.out_dir, "per_sample_segmentation.csv"), "w", newline="") as f:
        wcsv = csv.writer(f)
        wcsv.writerow(["sample"] + list(models_to_eval.keys()))
        for i in range(N_TEST):
            wcsv.writerow([i] + [per_sample[m]["dice"][i] for m in models_to_eval])

    with open(os.path.join(args.out_dir, "full_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nSaved outputs to {args.out_dir}")
    print("Done.")


if __name__ == "__main__":
    main()
