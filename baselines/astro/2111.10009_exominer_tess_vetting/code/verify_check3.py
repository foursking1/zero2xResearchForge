#!/usr/bin/env python3
"""Minimal judge-facing spot-check: reproduce the 3 critical numbers.

Run:  python3 verify_check3.py
Output matches results/check3.txt and results/metrics.json.
"""
from data_loader import load_exominer_vetting

SCORE = "ExoMiner Score"
MES = "MES"

df, path, digest = load_exominer_vetting()

total_rows = df.shape[0]                           # pandas data rows (project convention: 11,289)
n_gt_099 = int((df[SCORE] > 0.99).sum())
n_low_mes_gt_099 = int(((df[MES] < 10.5) & (df[SCORE] > 0.99)).sum())

print(f"data file : {path}")
print(f"sha256    : {digest}")
print()
print("1. total rows (pandas data rows) :", total_rows)
print("2. TCEs with score > 0.99         :", n_gt_099)
print("3. MES < 10.5 AND score > 0.99    :", n_low_mes_gt_099)

assert total_rows == 11289
assert n_gt_099 == 1070
assert n_low_mes_gt_099 == 30
print("\n[OK] all three numbers verified.")