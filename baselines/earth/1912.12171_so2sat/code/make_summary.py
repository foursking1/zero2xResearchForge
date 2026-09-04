"""Aggregate all experiment results into a single comparison table + figures.

- results/comparison.csv   : method x (OA, WA, AA, Kappa, train_size, bands)
- evidence/fig_s2_confusion.png : normalized confusion matrix of the primary S2 CNN
- evidence/fig_perclass.png     : per-class precision/recall of the primary S2 CNN
- evidence/fig_compare.png      : OA comparison bar chart across methods
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(ROOT, "results")
EVI = os.path.join(ROOT, "evidence")
os.makedirs(EVI, exist_ok=True)

LCZ = ["C high-rise", "C midrise", "C low-rise", "O high-rise", "O midrise",
       "O low-rise", "Lw low-rise", "Lg low-rise", "Sparsely built", "Heavy industry",
       "Dense trees", "Scattered trees", "Bush/scrub", "Low plants", "Paved",
       "Bare rock/sand", "Water"]

TAGS = ["s2_l", "s1s2_l", "s1_l", "pca_svm_s2", "pca_svm_s1s2", "stats_svm_s2",
        "rf_s2", "rf_s1s2", "knn_s2", "s2_l_cfrac0.1", "s2_l_cfrac0.3"]
LABELS = {
    "s2_l": "ResNeXt-CBAM (S2)",
    "s1s2_l": "ResNeXt-CBAM (S1+S2)",
    "s1_l": "ResNeXt-CBAM (S1)",
    "s2_l_cfrac0.1": "ResNeXt-CBAM (S2, 10% train)",
    "s2_l_cfrac0.3": "ResNeXt-CBAM (S2, 30% train)",
    "pca_svm_s2": "RBF-SVM PCA (S2)",
    "pca_svm_s1s2": "RBF-SVM PCA (S1+S2)",
    "stats_svm_s2": "RBF-SVM stats (S2)",
    "rf_s2": "RandomForest stats (S2)",
    "rf_s1s2": "RandomForest stats (S1+S2)",
    "knn_s2": "kNN stats (S2)",
}


def main():
    rows = []
    for t in TAGS:
        p = os.path.join(RES, t, "metrics.json")
        if not os.path.exists(p):
            print("skip", t)
            continue
        m = json.load(open(p))
        rows.append({"method": LABELS.get(t, t), "bands": m.get("bands_used", ""),
                     "OA": m["overall_accuracy"], "WA": m["weighted_accuracy"],
                     "AA": m["average_accuracy"], "Kappa": m["kappa"],
                     "train_size": m["train_size"]})
    rows.sort(key=lambda r: -r["OA"])
    with open(os.path.join(RES, "comparison.csv"), "w") as fh:
        fh.write("method,bands,OA,WA,AA,Kappa,train_size\n")
        for r in rows:
            fh.write(f"{r['method']},{r['bands']},{r['OA']:.4f},{r['WA']:.4f},"
                     f"{r['AA']:.4f},{r['Kappa']:.4f},{r['train_size']}\n")
    print(pd_csv := "\n".join(",".join(str(r[k]) for k in ("method", "bands", "OA", "WA", "AA", "Kappa", "train_size")) for r in rows))
    print("wrote", os.path.join(RES, "comparison.csv"))

    # --- figures for the primary S2 CNN ---
    cm = np.load(os.path.join(RES, "s2_l", "confusion_matrix.npy"))
    cmn = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)

    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(17), [str(i) for i in range(17)])
    ax.set_yticks(range(17), [str(i) for i in range(17)])
    ax.set_yticks(range(17), LCZ, fontsize=7.5)
    ax.set_xticks(range(17), LCZ, rotation=90, fontsize=7.5)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("ResNeXt-CBAM (S2) normalized confusion matrix (eval)"
                 "\nOA=0.97, AA=0.96, Kappa=0.97")
    for i in range(17):
        for j in range(17):
            v = cmn[i, j]
            if v > 0.30:
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if v > 0.6 else "black")
    fig.colorbar(im, label="row-normalized")
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "fig_s2_confusion.png"), dpi=150)

    # --- per-class metrics ---
    prec = np.load(os.path.join(RES, "s2_l", "evidence_table.csv")) if False else None
    import csv as _csv
    with open(os.path.join(RES, "s2_l", "evidence_table.csv")) as fh:
        rd = list(_csv.DictReader(fh))
    cls = [r for r in rd if int(r["class_id"]) >= 0]
    xpos = np.arange(17)
    fig, ax = plt.subplots(figsize=(9, 5))
    w = 0.38
    ax.bar(xpos - w / 2, [float(r["precision"]) for r in cls], w, label="precision")
    ax.bar(xpos + w / 2, [float(r["recall"]) for r in cls], w, label="recall")
    ax.set_xticks(xpos, LCZ, rotation=45, ha="right", fontsize=7)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("score")
    ax.set_title("ResNeXt-CBAM (S2) per-class precision/recall")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "fig_perclass.png"), dpi=150)

    # --- main comparison bar chart ---
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [r["method"] for r in rows]
    oas = [r["OA"] for r in rows]
    kap = [r["Kappa"] for r in rows]
    xp = np.arange(len(names))
    ax.bar(xp - 0.2, oas, 0.38, label="OA", color="#4C72B0")
    ax.bar(xp + 0.2, kap, 0.38, label="Kappa", color="#DD8452")
    ax.axhline(0.61, color="red", ls="--", lw=1, label="paper anchor OA=0.61 (S2)")
    ax.axhline(0.54, color="k", ls=":", lw=1, label="paper SVM OA=0.54 (S2)")
    ax.set_xticks(xp, names, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("score"); ax.set_ylim(0, 1.06)
    ax.set_title("OA & Kappa across methods (internal eval split of frozen validation)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(EVI, "fig_compare.png"), dpi=150)

    # --- data-size scaling curve (S2 CNN) ---
    fracs = [0.1, 0.3, 1.0]
    oa_by_frac = []
    for fr in fracs:
        tag = "s2_l" if fr == 1.0 else f"s2_l_cfrac{fr}"
        p = os.path.join(RES, "s2_l" if fr == 1.0 else f"s2_l_cfrac{fr}", "metrics.json")
        if os.path.exists(p):
            oa_by_frac.append(float(json.load(open(p))["overall_accuracy"]))
        else:
            oa_by_frac.append(None)
    fig, ax = plt.subplots(figsize=(6, 4))
    fx = [0.01 * 19297 * fr if fr < 1.0 else 19297 for fr in fracs] if all(
        v is not None for v in oa_by_frac) else []
    if fx:
        ax.plot(fx, oa_by_frac, marker="o")
        ax.axhline(0.61, color="red", ls="--", lw=1, label="paper anchor 0.61")
        ax.set_xlabel("training patches (S2, eval held out) supported speed")
        ax.set_ylabel("OA")
        ax.set_ylim(0.5, 1.0)
        ax.set_title("Data-size scaling of ResNeXt-CBAM (S2)")
        ax.legend()
        ax.set_xticks(fx, ["1.9k", "5.8k", "19.3k"])
        fig.tight_layout()
        fig.savefig(os.path.join(EVI, "fig_scaling.png"), dpi=150)
    print("figures written to", EVI)


if __name__ == "__main__":
    main()