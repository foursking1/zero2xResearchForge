#!/usr/bin/env python3
"""01_verify_data.py — B-check #1: decode frozen CIFAR-10 pickles and verify:
    - train 50,000, exactly 5,000 per class
    - test 10,000, exactly 1,000 per class
    - images 32x32x3 uint8
Writes agent_solution/results/data_verification.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import verify_global_stats, META, get_data_dir

def main():
    ddir = get_data_dir()
    print(f"[verify] data dir = {ddir}")
    stats = verify_global_stats(ddir)
    ok_train = (stats["train_total"] == 50000
                and all(c == 5000 for c in stats["train_per_class"]))
    ok_test = (stats["test_total"] == 10000
               and all(c == 1000 for c in stats["test_per_class"]))
    ok_img = tuple(stats["img_shape"]) == (32, 32, 3)
    stats["verify"] = {"train_ok": ok_train, "test_ok": ok_test, "img_ok": ok_img}
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "data_verification.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    print(f"[verify] train_ok={ok_train} test_ok={ok_test} img_ok={ok_img}")
    for i, m in enumerate(META):
        print(f"  class {i:2d} {m:10s}: train={stats['train_per_class'][i]} test={stats['test_per_class'][i]}")
    if not (ok_train and ok_test and ok_img):
        sys.exit(1)

if __name__ == "__main__":
    main()