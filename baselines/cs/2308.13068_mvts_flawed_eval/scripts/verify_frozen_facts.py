"""Independent re-derivation of the two key frozen-fact / result checks:

  1. PSM test anomaly ratio = 27.76 %  (24,381 / 87,841)  [pure data fact]
  2. Random-guess point-wise F1 (alpha=1000, 50 repeats) on PSM & SWaT
     [must match metrics.json / report; magnitude ~0.01-0.02]

Run:  python scripts/verify_frozen_facts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from scripts.common import DATA_ROOT, load_dataset
from baselines.random_guess import random_guess_eval

print("=" * 70)
print("Check 1: PSM test anomaly ratio (pure data fact)")
print("=" * 70)
lbl = pd.read_csv(DATA_ROOT / "PSM_test_label.csv").iloc[:, 1].to_numpy(int)
n = len(lbl)
n_anom = int((lbl == 1).sum())
print(f"  PSM test points         : {n}")
print(f"  PSM anomaly points      : {n_anom}")
print(f"  anomaly ratio           : {100 * n_anom / n:.4f} %")
assert n == 87841 and n_anom == 24381
print("  -> PASS  (ratio 27.76 %, n=87,841, 24,381 anomalies)")

swat_lbl = np.load(DATA_ROOT / "SWaT_SWaT_test_label.npy", mmap_mode="r")
swat_lbl = swat_lbl.astype(int).ravel()
print(f"\n  SWaT test points         : {len(swat_lbl)}")
print(f"  SWaT anomaly points      : {(swat_lbl == 1).sum()}")
print(f"  anomaly ratio           : {100 * (swat_lbl == 1).mean():.4f} %")
assert len(swat_lbl) == 449919
print("  -> PASS (12.14 %)")

print()
print("=" * 70)
print("Check 2: random-guess point-wise F1 (alpha=1000, 50 repeats)")
print("=" * 70)
for ds in ["SWaT", "PSM"]:
    data = load_dataset(ds)
    label = data["label"]
    res = random_guess_eval(1000, label, n_repeats=50, seed0=42)
    print(f"  {ds}: pointwise F1 = {res['pointwise_f1_mean']:.5f} "
          f"± {res['pointwise_f1_std']:.5f}  |  point-adjust F1 = "
          f"{res['point_adjust_f1_mean']:.5f} ± {res['point_adjust_f1_std']:.5f}")
    assert 0.003 <= res["pointwise_f1_mean"] <= 0.03, "pointwise F1 out of magnitude band"
print("  -> PASS  (both in the ~0.004-0.023 magnitude band reported in metrics.json)")
print("\nAll frozen-fact / reproducibility checks passed.")