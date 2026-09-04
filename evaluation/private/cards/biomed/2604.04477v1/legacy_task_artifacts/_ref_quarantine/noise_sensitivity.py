"""
Noise sensitivity analysis for the frozen MVis-Fold checkpoint.

Tests the same frozen test samples (seeds 300..349, max_branches=15) at three
SRUS noise levels (0.05, 0.1, 0.3) to assess robustness of the segmentation
metrics. The model was trained with noise_level=0.1.

This provides the sensitivity/robustness component of the evidence (does the
metric degrade gracefully rather than catastrophically?).

Usage:
    python noise_sensitivity.py [--n_test 50] [--data_root F:/dataset/2604.04477v1]
"""

import argparse
import json
import os
import sys

import numpy as np
import torch

DEFAULT_DATA_ROOT = r"F:/dataset/2604.04477v1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_test", type=int, default=50)
    ap.add_argument("--data_root", type=str, default=DEFAULT_DATA_ROOT)
    ap.add_argument("--out_dir", type=str,
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    ap.add_argument("--shape", type=int, nargs=3, default=[16, 32, 32])
    args = ap.parse_args()

    root = os.path.abspath(args.data_root)
    sys.path.insert(0, os.path.join(root, "src"))
    from models.mvisfold import build_model
    from data.synthetic import VascularTreeGenerator, generate_sruse_channels
    from evaluate.metrics import compute_all_metrics

    os.makedirs(args.out_dir, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    SHAPE = tuple(args.shape)
    N = args.n_test
    SEED = 300

    model, _, _ = build_model(in_channels=6, use_small=True, device=device)
    ckpt = torch.load(os.path.join(root, "checkpoints", "stage1_best.pth"),
                      map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    noise_levels = [0.05, 0.1, 0.3]
    results = {}
    for nl in noise_levels:
        dices, senns, accs = [], [], []
        with torch.no_grad():
            for i in range(N):
                gen = VascularTreeGenerator(shape=SHAPE, max_branches=15, seed=SEED + i)
                phantom = gen.generate()
                ch = generate_sruse_channels(phantom, noise_level=nl, seed=SEED + i + 5000)
                x = torch.from_numpy(ch).unsqueeze(0).float().to(device)
                out = model(x)[0, 0].cpu().numpy()
                m = compute_all_metrics(out, phantom.volume)
                dices.append(m["dice"]); senns.append(m["sensitivity"]); accs.append(m["accuracy"])
        results[nl] = {
            "dice_mean": round(float(np.mean(dices)), 4),
            "dice_std": round(float(np.std(dices)), 4),
            "sens_mean": round(float(np.mean(senns)), 4),
            "acc_mean": round(float(np.mean(accs)), 4),
        }
        print(f"noise={nl}: Dice={results[nl]['dice_mean']:.4f}+/-{results[nl]['dice_std']:.4f} "
              f"Sens={results[nl]['sens_mean']:.4f} Acc={results[nl]['acc_mean']:.4f}")

    with open(os.path.join(args.out_dir, "noise_sensitivity.json"), "w") as f:
        json.dump({"n_test": N, "shape": list(SHAPE), "checkpoint_stage": ckpt.get("stage"),
                   "results": results}, f, indent=2)
    print(f"Saved noise_sensitivity.json to {args.out_dir}")


if __name__ == "__main__":
    main()
