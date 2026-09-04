"""Run 5-fold CV (Case 3) with physics-informed augmentation."""
import json
import numpy as np
from data_loader import load_data
from train_eval import cross_validate

d = load_data()
agg, folds = cross_validate(d["X_exp"], d["y_exp"], d["X_theo"], d["y_theo"],
                            d["tw"], use_aug=True, verbose=True, device="cpu")

out = {
    "agg": agg,
    "per_fold": [{"fold": f["fold"], "accuracy": f["accuracy"],
                  "f1_micro": f["f1_micro"], "f1_macro": f["f1_macro"],
                  "test_idx": f["test_idx"].tolist(),
                  "pred": f["pred"].tolist(), "true": f["true"].tolist()}
                 for f in folds],
}
with open("../results/cv_aug.json", "w") as fp:
    json.dump(out, fp, indent=2, default=float)
np.save("../results/cv_aug.npy", out, allow_pickle=True)
print("saved ../results/cv_aug.json")
print(json.dumps(agg, indent=2, default=float))
