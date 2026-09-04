#!/usr/bin/env python3
"""Compute per-class and overall metrics from saved test predictions, and emit
the evidence artifacts required by the task:
  - results/evidence_table.csv
  - results/metrics.json
  - confusion matrices (.npy, .csv) and a summary markdown
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    HAS_MPL = False

CLASS_NAMES = [
    "airplane", "airport", "baseball_diamond", "basketball_court", "beach",
    "bridge", "chaparral", "church", "circular_farmland", "cloud",
    "commercial_area", "dense_residential", "desert", "forest", "freeway",
    "golf_course", "ground_track_field", "harbor", "industrial_area",
    "intersection", "island", "lake", "meadow", "medium_residential",
    "mobile_home_park", "mountain", "overpass", "palace", "parking_lot",
    "railway", "railway_station", "rectangular_farmland", "river",
    "roundabout", "runway", "sea_ice", "ship", "snowberg",
    "sparse_residential", "stadium", "storage_tank", "tennis_court",
    "terrace", "thermal_power_station", "wetland",
]


def metrics_from_confusion(conf, labels_out=None):
    """conf[c,p] = # true c predicted p (45x45). Returns per-class stats."""
    n = conf.shape[0]
    tp = np.diag(conf).astype(float)
    fn = conf.sum(1) - tp          # actual c but predicted other
    fp = conf.sum(0) - tp          # predicted c but actual other
    tn = conf.sum() - (tp + fn + fp)
    precision = tp / np.maximum(tp + fp, 1e-12)
    recall = tp / np.maximum(tp + fn, 1e-12)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    accuracy = (tp + tn) / np.maximum(conf.sum(), 1e-12)
    rows = []
    for c in range(n):
        rows.append({
            "class_id": c,
            "class_name": CLASS_NAMES[c] if c < len(CLASS_NAMES) else str(c),
            "tp": int(tp[c]), "fp": int(fp[c]), "tn": int(tn[c]),
            "fn": int(fn[c]),
            "precision": round(float(precision[c]), 6),
            "recall": round(float(recall[c]), 6),
            "f1": round(float(f1[c]), 6),
            "accuracy": round(float(accuracy[c]), 6),
        })
    return rows, {"tp": tp, "fn": fn, "fp": fp, "tn": tn}


def build_evidence(files, split_csvs, metrics_out, evidence_csv):
    rows_all = []
    per_ratio_metrics = {}
    for f in files:
        data = np.load(f, allow_pickle=True)
        fname = os.path.basename(f)
        # parse arch_r_X_XX_s NNNNNNN from preds_resnet18_r0.10_s20260813.npz
        parts = fname.replace(".npz", "").split("_")
        # parts[0]=preds parts[1]=arch parts[2]=r parts[3]=ratio parts[4]=s parts[5]=seed
        arch = parts[1]
        ratio = float(parts[3].lstrip("r"))
        seed = int(parts[5].lstrip("s"))
        conf = data["confusion"]
        rows, _ = metrics_from_confusion(conf)
        total = int(conf.sum())
        oa = 100.0 * np.trace(conf) / max(total, 1)
        for r in rows:
            r["split"] = "%02d%%train" % int(ratio * 100)
            r["train_ratio"] = ratio
        overall = {
            "split": "%02d%%train" % int(ratio * 100),
            "train_ratio": ratio,
            "class_id": -1,
            "class_name": "overall",
            "tp": int(np.trace(conf)), "fp": int(conf.sum() - np.trace(conf)),
            "tn": 0, "fn": 0,
            # macro per-class stats
            "precision": round(float(np.mean([x["precision"] for x in rows])), 6),
            "recall": round(float(np.mean([x["recall"] for x in rows])), 6),
            "f1": round(float(np.mean([x["f1"] for x in rows])), 6),
            "accuracy": round(float(oa / 100.0), 6),
        }
        rows_all.append(overall)
        rows_all.extend(rows)
        per_ratio_metrics.setdefault(ratio, {}).setdefault("runs", []).append(oa)
        per_ratio_metrics[ratio]["arch"] = arch[0] if isinstance(arch, (str,)) else arch
        per_ratio_metrics[ratio]["seeds"] = [seed]
        per_ratio_metrics[ratio]["oa_single"] = oa
        per_ratio_metrics[ratio]["confusion"] = conf.tolist()
        print("[%s] ratio=%.2f seed=%d OA=%.2f (n=%d)"
              % (fname, ratio, seed, oa, total))

    # aggregate over seeds for each ratio
    summary = {}
    for ratio, d in per_ratio_metrics.items():
        oas = d["runs"]
        seeds = d["seeds"]
        summary["ratio_%.2f" % ratio] = {
            "seed": seeds,
            "oa_runs": oas,
            "mean_oa": round(float(np.mean(oas)), 4),
            "std_oa": round(float(np.std(oas)), 4),
            "n_runs": len(oas),
        }
    with open(metrics_out, "w") as f:
        json.dump(summary, f, indent=2)

    ev_df = pd.DataFrame(rows_all)
    ev_df.to_csv(evidence_csv, index=False)
    print("Evidence table written to", evidence_csv, "shape", ev_df.shape)
    return ev_df


def plot_confusion(conf, title, outpng):
    if not HAS_MPL:
        print("matplotlib unavailable; skipping plot", outpng)
        return
    fig, ax = plt.subplots(figsize=(16, 14))
    im = ax.imshow(conf, cmap="viridis")
    ax.set_xticks(range(45)); ax.set_yticks(range(45))
    ax.set_xticklabels(CLASS_NAMES, rotation=90, fontsize=6)
    ax.set_yticklabels(CLASS_NAMES, fontsize=6)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(outpng, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--arch", default="resnet18")
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.results,
                                          "preds_%s_r*.npz" % args.arch)))
    if not files:
        raise SystemExit("no preds files found for arch %s" % args.arch)
    metrics_out = os.path.join(args.results, "metrics.json")
    evidence_csv = os.path.join(args.results, "evidence_table.csv")
    ev = build_evidence(files, None, metrics_out, evidence_csv)

    # confusion CSVs for each ratio
    for ratio, d in json.load(open(metrics_out)).items():
        pass

    # also save per-ratio aggregate confusion as CSV (average of runs)
    for f in files:
        data = np.load(f, allow_pickle=True)
        parts = os.path.basename(f).replace(".npz", "").split("_")
        ratio = float(parts[3].lstrip("r"))
        seed = int(parts[5].lstrip("s"))
        conf = data["confusion"]
        np.save(os.path.join(args.results, "confusion_r%.2f_s%d.npy"
                             % (ratio, seed)), conf)
        pd.DataFrame(conf, index=CLASS_NAMES, columns=CLASS_NAMES).to_csv(
            os.path.join(args.results, "confusion_r%.2f_s%d.csv"
                         % (ratio, seed)))
        oa = 100.0 * np.trace(conf) / conf.sum()
        plot_confusion(conf, "RESISC45 confusion matrix, %d%% train (seed %d, "
                       "OA=%.2f%%)" % (int(ratio * 100), seed, oa),
                       os.path.join(args.results, "confusion_r%.2f_s%d.png"
                                    % (ratio, seed)))


if __name__ == "__main__":
    main()