"""End-to-end pipeline: methods -> protocols -> random baseline -> results.

Produces:
  results/evidence_table.csv   (dataset x method x threshold x protocol F1 table)
  results/metrics.json          (all key metrics incl. anchor-check facts)
  results/predictions/*.npz     (scores/predictions per dataset x method)
  figures/*.png                 (summary plots)
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.common import (load_dataset, impute_nan_mean, zscore_fit,
                            zscore_transform, best_threshold_oracle,
                            threshold_train_fixed, pointwise_metrics_from_scores)
from method.pca_baseline import PCAReconstructionBaseline, MahalanobisBaseline
from method.gru_autoencoder import GRUAutoencoderDetector
from protocols.eval_protocols import evaluate_all, point_adjust_f1
from baselines.random_guess import random_guess_eval

RNG_SEED = 42
N_REPEATS_RG = 50
ALPHA_FIXED = 1000


def evaluate_scores(name: str, family: str, s_tr: np.ndarray, s_te: np.ndarray,
                    data: dict, out_dir: Path, tag: str = ""):
    """Threshold + full protocol evaluation for fixed train/test score vectors."""
    thresholds = {
        "oracle": best_threshold_oracle(s_te, data["label"])[0],
        "train_mean+3std": threshold_train_fixed(s_tr, "mean3std"),
        "train_q99": threshold_train_fixed(s_tr, "quantile99"),
    }
    records = []
    method_out = f"{name}{tag}" if tag else name
    for tname, thresh in thresholds.items():
        pred = (s_te >= thresh).astype(int)
        ev = evaluate_all(pred, data["label"])
        row = {
            "dataset": data["name"], "method": method_out, "family": family,
            "threshold": tname, "threshold_value": float(thresh),
            "f1_pointwise": ev["pointwise"]["f1"],
            "precision_pointwise": ev["pointwise"]["precision"],
            "recall_pointwise": ev["pointwise"]["recall"],
            "f1_point_adjust": ev["point_adjust"]["f1"],
            "precision_point_adjust": ev["point_adjust"]["precision"],
            "recall_point_adjust": ev["point_adjust"]["recall"],
            "f1_event_F1E": ev["event_F1E"]["f1e"],
            "recall_event_F1E": ev["event_F1E"]["recall_e"],
            "far_event_F1E": ev["event_F1E"]["far"],
            "n_pred_positive": int(pred.sum()),
            "tag": tag,
        }
        records.append(row)
        print(f"      {method_out} [{tname}]: F1pw={row['f1_pointwise']:.4f} "
              f"F1pa={row['f1_point_adjust']:.4f} F1E={row['f1_event_F1E']:.4f}")
    np.savez_compressed(
        out_dir / f"{data['name']}_{name}{tag}.npz".replace('&', '__'),
        score_train=s_tr, score_test=s_te, label=data["label"])
    return records


def run_method(name: str, family: str, detector, data: dict, out_dir: Path):
    """Fit detector on train, score train+test, evaluate all thresholds/protocols."""
    print(f"  - fitting {name} ...")
    t0 = time.time()
    detector.fit(data["train"])
    t_fit = time.time() - t0

    print(f"  - scoring {name} ...")
    s_tr = detector.score(data["train"])
    s_te = detector.score(data["test"])

    records = evaluate_scores(name, family, s_tr, s_te, data, out_dir)
    return records, dict(fit_time_s=t_fit)


def main():
    t_start = time.time()
    (ROOT / "results" / "predictions").mkdir(parents=True, exist_ok=True)
    all_records = []
    metrics = {"datasets": {}, "random_guess": {}}

    for dsname in ["SWaT", "PSM"]:
        print(f"\n=== {dsname} ===")
        data = load_dataset(dsname)
        data["train"] = impute_nan_mean(data["train"])
        lbl = data["label"]
        ds_metrics = {
            "n_train": int(data["train"].shape[0]),
            "n_test": int(data["test"].shape[0]),
            "n_channels": int(data["train"].shape[1]),
            "n_anomaly_test": int((lbl == 1).sum()),
            "anomaly_ratio_test": float((lbl == 1).mean()),
        }
        # ---- methods ----
        recs = []
        md = data.copy()

        pca = PCAReconstructionBaseline(variance=0.95, smooth=5, seed=RNG_SEED, score_std="cholstd")
        r, meta = run_method("PCA", "simple", pca, md, ROOT / "results" / "predictions")
        recs += r; ds_metrics["pca_n_components"] = int(pca.pca_.n_components_); ds_metrics["pca_fit_time_s"] = meta["fit_time_s"]

        pca_u = PCAReconstructionBaseline(variance=0.95, smooth=5, seed=RNG_SEED, score_std="uniform")
        r, meta = run_method("PCA-uniform", "simple", pca_u, md, ROOT / "results" / "predictions")
        recs += r  # sensitivity: uniform residual without per-channel equalization

        mah = MahalanobisBaseline(smooth=5)
        r, meta = run_method("Mahalanobis", "simple", mah, md, ROOT / "results" / "predictions")
        recs += r; ds_metrics["mah_fit_time_s"] = meta["fit_time_s"]

        gru = GRUAutoencoderDetector(length=100, train_stride=20, test_stride=25,
                                     hidden=32, epochs=6, batch_size=512,
                                     lr=1e-3, smooth=5, seed=RNG_SEED, device="cpu")
        print(f"  - fitting GRU-AE (primary) ...")
        t0 = time.time()
        gru.fit(md["train"], verbose=True)
        ds_metrics["gru_epochs"] = gru.epochs
        ds_metrics["gru_fit_time_s"] = time.time() - t0
        print("  - scoring GRU-AE (raw) ...")
        g_tr = gru.score(md["train"], per_channel_std=False)
        g_te = gru.score(md["test"], per_channel_std=False)
        recs += evaluate_scores("GRU-AE", "deep", g_tr, g_te, md, ROOT / "results" / "predictions")
        print("  - scoring GRU-AE (per-channel std, robustness) ...")
        gc_tr = gru.score(md["train"], per_channel_std=True)
        gc_te = gru.score(md["test"], per_channel_std=True)
        recs += evaluate_scores("GRU-AE", "deep", gc_tr, gc_te, md, ROOT / "results" / "predictions",
                                tag="-cholstd")

        # ---- random guess baseline ----
        alpha2 = int(round(0.01 * lbl.size))
        rg = {}
        for tag, alpha in [("a1000", ALPHA_FIXED), ("a1pct", alpha2)]:
            rg[tag] = random_guess_eval(alpha, lbl, n_repeats=N_REPEATS_RG, seed0=RNG_SEED)
            print(f"  random-guess {tag} (alpha={alpha}): "
                  f"F1pw={rg[tag]['pointwise_f1_mean']:.4f} "
                  f"F1pa={rg[tag]['point_adjust_f1_mean']:.4f} "
                  f"gap={rg[tag]['gap_f1pa_minus_f1pw']:.4f}")

        ds_metrics["random_guess"] = rg
        metrics["datasets"][dsname] = ds_metrics
        all_records += recs

    # ---- aggregate table ----
    df = pd.DataFrame(all_records)
    df.to_csv(ROOT / "results" / "evidence_table.csv", index=False)

    metrics["meta"] = {
        "n_repeats_random_guess": N_REPEATS_RG,
        "alpha_fixed": ALPHA_FIXED,
        "seed": RNG_SEED,
        "protocols": ["pointwise", "point_adjust", "event_F1E"],
        "threshold_types": ["oracle", "train_mean+3std", "train_q99"],
        "total_runtime_s": time.time() - t_start,
        "note_threshold": ("oracle = threshold maximizing point-wise F1 on the TEST "
                           "set (declared oracle/lower-bound-agnostic; follows arXiv:"
                           "2308.13068 Table 1 convention). train_* = fixed threshold "
                           "fit on TRAIN scores only."),
    }
    with open(ROOT / "results" / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nwrote:", ROOT / "results" / "evidence_table.csv")
    print("wrote:", ROOT / "results" / "metrics.json")


if __name__ == "__main__":
    main()