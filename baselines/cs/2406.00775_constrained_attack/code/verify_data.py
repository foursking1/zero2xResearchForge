"""
Independent verification of the two rubric checkpoints:

1. url.csv scale & balance (pure data facts): 11,430 rows x 64 cols,
   is_phishing mean ~ 0.50; feature order matches url_features.csv.
2. Constraint-satisfaction rate recomputed from the frozen constraint
   implementation (the attack code already evaluates this on the generated
   candidates; this script exports the clean-data feasibility baseline and
   the constraint set size for cross-checking).
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code"))

from constraints import URLConstraintSet
from datautils import load_url

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    df = load_url(os.path.join(ROOT, "data", "url.csv"))
    meta = pd.read_csv(os.path.join(ROOT, "data", "url_features.csv"))
    cset = URLConstraintSet(os.path.join(ROOT, "data", "url_features.csv"))

    out = {
        "url_csv_shape": list(df.shape),
        "expected_shape": [11430, 64],
        "is_phishing_mean": float(df["is_phishing"].mean()),
        "class_counts": {str(k): int(v) for k, v in df["is_phishing"].value_counts().items()},
        "features_match_url_features_csv": bool(list(df.columns[:-1]) == list(meta["feature"])),
        "n_features": int(df.shape[1] - 1),
        "n_relation_constraints": int(len(cset.lin_c)) + int(len(cset.imp_a)),
        "clean_data_feasibility": float(
            cset.is_feasible(torch.tensor(df.iloc[:, :-1].to_numpy())).float().mean()),
    }
    print(json.dumps(out, indent=2))
    res_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "results", "urldata_check.json")
    with open(res_path, "w") as f:
        json.dump(out, f, indent=2)
    print("wrote", res_path)


if __name__ == "__main__":
    main()