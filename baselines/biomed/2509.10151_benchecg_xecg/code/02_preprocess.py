#!/usr/bin/env python3
"""Step 2 - frozen-data pre-processing + auxiliary target construction.

- Reads train/validation parquet (no labels present in the frozen schema).
- Down-samples the native 500 Hz / 10 s signals to the official 100 Hz setting
  (factor 5) with a box-car anti-aliasing filter.
- Fits per-lead z-score statistics on the TRAINING split ONLY (anti-leakage,
  per the task's "normalization statistics may only be fitted on the train
  split" rule) and applies them to both splits.
- Builds the only real targets available in the frozen package (sex, age>=65)
  and caches everything as arrays for fast re-runs of the model scripts.

NOTE: this step intentionally does NOT produce diagnostic superclass targets,
because no diagnostic label column exists in the frozen parquet schema.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (
    SEED,
    apply_normalization,
    build_targets,
    downsample,
    fit_normalization,
    load_signals_and_meta,
    save_json,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "results")
os.makedirs(CACHE, exist_ok=True)
OUT_NPZ = os.path.join(CACHE, "preprocessed.npz")

FACTOR = 5  # 500 Hz -> 100 Hz


def main() -> None:
    print("loading train split ...")
    Xtr, metr = load_signals_and_meta("train")
    print(f"  train signal tensor: {Xtr.shape} {Xtr.dtype}")
    print("loading validation split ...")
    Xva, meva = load_signals_and_meta("validation")
    print(f"  val signal tensor:   {Xva.shape} {Xva.dtype}")

    # downsample + normalize (train-only fit)
    Xtr = downsample(Xtr, FACTOR)
    Xva = downsample(Xva, FACTOR)
    stats = fit_normalization(Xtr)
    Xtr = apply_normalization(Xtr, stats)
    Xva = apply_normalization(Xva, stats)

    # auxiliary targets present in the frozen package
    ttr = build_targets(metr).to_numpy(float).astype(np.int8)
    tva = build_targets(meva).to_numpy(float).astype(np.int8)
    target_names = list(build_targets(metr).columns)

    label_stats = {
        "title": "AUXILIARY targets only (real columns present in frozen schema)",
        "targets_available": target_names,
        "diagnostic_superclass_targets_available": False,
        "train": {
            c: {"pos": int((ttr[:, j] == 1).sum()), "neg": int((ttr[:, j] == 0).sum())}
            for j, c in enumerate(target_names)
        },
        "validation": {
            c: {"pos": int((tva[:, j] == 1).sum()), "neg": int((tva[:, j] == 0).sum())}
            for j, c in enumerate(target_names)
        },
    }

    np.savez_compressed(
        OUT_NPZ,
        Xtrain=Xtr, Xval=Xva, ttrain=ttr, tval=tva,
        train_ids=metr["ecg_id"].to_numpy(), val_ids=meva["ecg_id"].to_numpy(),
    )
    save_json(
        {
            "preprocessing": {
                "native_fs": 500, "target_fs": 100, "downsample_factor": FACTOR,
                "normalization": "per-lead z-score, fitted on TRAIN split only",
                "normalization_stats": stats,
                "signal_tensor_train": list(Xtr.shape),
                "signal_tensor_val": list(Xva.shape),
                "leads": 12, "samples_per_lead": int(Xtr.shape[1]),
            },
            "label_stats_for_evidence": label_stats,
        },
        os.path.join(CACHE, "preprocessing.json"),
    )
    print("cached", OUT_NPZ)
    print("label stats:", label_stats)
    print("normalization stats (fit on train only):", {k: np.round(v, 4) for k, v in stats.items()})


if __name__ == "__main__":
    main()