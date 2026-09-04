"""Step 5 — Self-verification mirroring the judge's evidence checks.

Checks performed deterministically on the frozen data:
  1. test split row count == 1999 (also train 62478 / valid 6942)
  2. re-compute the DDE + LR test accuracy from the frozen CSVs (fast, CPU,
     deterministic) and confirm it matches results/metrics.json to 1e-6
  3. confirm evidence_table.csv is row-consistent with metrics.json
  4. confirm data SHA-256 values match the frozen manifest
"""
import os
import sys
import json
import csv
import hashlib
import importlib.util

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from common import load_split, set_seed, ensure_dir, find_data_dir

HERE = os.path.dirname(__file__)
RESULTS = ensure_dir(os.path.join(HERE, "..", "results"))
SEED = 2024
EXPECTED_SHA = {
    "train": "7236c5c98bfbf621fa14256d6ebf8731037f26a55458778dc57ab6a31f018f76",
    "valid": "1b01ec51e1bc625078b48307adee54a3853fb97cf8c3e55fae35c86317be179c",
    "test": "ab535824c06d6bea13da3d9d4332ca5e26ffa00fe54260a00a21ba644beab4c8",
}


def _load_mod(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"02_feature_models.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main():
    set_seed(SEED)
    ok = True

    # ---- check 1: split counts + positive ratios ----
    print("[verify] split sizes:")
    for split, expected_n in [("train", 62478), ("valid", 6942), ("test", 1999)]:
        df = load_split(split)
        n = len(df)
        match = n == expected_n
        ok &= match
        print(f"   {split:6s} n={n:7d} (expect {expected_n}) {'OK' if match else '!!MISMATCH!!'}")

    # ---- check 2: DDE + LR test accuracy re-run ----
    fm = _load_mod("feature_models")
    train, valid, test = load_split("train"), load_split("valid"), load_split("test")
    Xtr = fm.dde_features(train["sequence"].tolist())
    ytr = train["label"].values
    Xva = fm.dde_features(valid["sequence"].tolist())
    yva = valid["label"].values
    Xte = fm.dde_features(test["sequence"].tolist())
    yte = test["label"].values
    sc = StandardScaler().fit(Xtr)
    Xtr, Xva, Xte = sc.transform(Xtr), sc.transform(Xva), sc.transform(Xte)
    best_c, _, _ = fm._select_C(Xtr, ytr, Xva, yva,
                                [1e-2, 3e-2, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0, 300.0], SEED)
    clf = LogisticRegression(C=best_c, max_iter=1000, solver="liblinear", random_state=SEED)
    clf.fit(Xtr, ytr)
    dde_acc = clf.score(Xte, yte) * 100.0

    with open(os.path.join(RESULTS, "metrics.json")) as f:
        metrics = json.load(f)
    reported = metrics["models"]["DDE"]["accuracy_pct"]
    rel_diff = abs(dde_acc - reported) / reported
    print(f"[verify] DDE+LR test acc recomputed={dde_acc:.6f}  "
          f"reported={reported:.6f}  rel_diff={rel_diff:.2e}")
    match = rel_diff <= 1e-6
    ok &= match

    # ---- check 3: evidence_table.csv consistency ----
    with open(os.path.join(RESULTS, "evidence_table.csv")) as f:
        rows = list(csv.DictReader(f))
    check = True
    for r in rows:
        mm = metrics["models"].get(r["model"])
        if mm is None or abs(float(r["accuracy"]) - mm["accuracy_pct"]) > 1e-9:
            check = False
    print(f"[verify] evidence_table.csv consistent with metrics.json: {check}")
    ok &= check

    # ---- check 4: sha256 ----
    d = find_data_dir()
    shaok = True
    for split, exp in EXPECTED_SHA.items():
        with open(os.path.join(d, f"solubility_{split}.csv"), "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        if h != exp:
            shaok = False
            print(f"   SHA mismatch on {split}")
    print(f"[verify] data SHA-256 match frozen manifest: {shaok}")
    ok &= shaok

    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()