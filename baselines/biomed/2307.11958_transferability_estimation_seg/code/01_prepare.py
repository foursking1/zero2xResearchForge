"""01_prepare.py -- build the 2-D slice database + inventory.

Reads the frozen NIfTI files (Spleen + Liver), extracts axial slices with a
deterministic foreground-biased sampler, caches uint8 arrays under work/cache,
and writes results/data_inventory.json + results/splits.json.
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA_ROOT, CACHE_DIR, RESULTS_DIR, CASES, SPLITS, load_case,
                    prepare_case, save_json, to_uint8, from_uint8)

PIX = 128
MAX_SLICES_TRAIN = 40   # per case, used for pretrain / fine-tune
MAX_SLICES_TEST = 400   # per case, used for held-out evaluation
SEED = 0


def main():
    print(f"DATA_ROOT = {DATA_ROOT}")
    assert os.path.isdir(DATA_ROOT), DATA_ROOT
    inventory = {"spleen": [], "liver": []}
    for organ in ("spleen", "liver"):
        for case in CASES[organ]:
            res = load_case(organ, case)
            hi = res["img"]
            record = {
                "case": case, "organ": organ,
                "orig_nz_img": res["orig_nz_img"],
                "usable_nz": hi.shape[2],
                "img_complete": res["img_complete"],
                "lab_complete": res["lab_complete"],
                "shape": list(res["shape"]),
                "pixdim_mm": [round(x, 4) for x in res["pixdim"]],
                "fg_voxels": int(np.count_nonzero(res["lab"])),
            }
            if res["lab"].max() > 1:
                record["label_values"] = [int(x) for x in np.unique(res["lab"]).tolist()]
            inventory[organ].append(record)
            print(f"  [{organ}] {case}: usable {res['img'].shape[2]}/{record['orig_nz_img']} slices, "
                  f"img_complete={record['img_complete']} lab_complete={record['lab_complete']}")

    # ---- cache train slices for each (organ, case) -------------------
    for organ in ("spleen", "liver"):
        for case in CASES[organ]:
            npz = os.path.join(CACHE_DIR, f"{organ}_{case}.npz")
            if os.path.exists(npz):
                continue
            imgs, labs, _ = prepare_case(organ, case, MAX_SLICES_TRAIN, seed=SEED, size=PIX)
            np.savez_compressed(npz, img=imgs, lab=labs)
            print(f"  cached {npz}  imgs{imgs.shape} fg%={(labs > 0).mean():.3f}")

    splits = {
        "protocol": {
            "source_task": "liver", "target_task": "spleen",  # primary direction
            "reverse": True,
            "note": "Primary: source pool pretrained on Liver, target = Spleen. "
                    "Reverse: source pool pretrained on Spleen, target = Liver.",
        },
        "pixel_size": PIX,
        "max_slices_train_per_case": MAX_SLICES_TRAIN,
        "seed": SEED,
        "spleen": {
            "train": SPLITS["spleen"][0], "test": SPLITS["spleen"][1],
            "note": "deterministic split; Liver never touches target Spleen at pretrain time",
        },
        "liver": {
            "train": SPLITS["liver"][0], "test": SPLITS["liver"][1],
        },
    }
    save_json(splits, os.path.join(RESULTS_DIR, "splits.json"))
    save_json(inventory, os.path.join(RESULTS_DIR, "data_inventory.json"))
    print("saved", os.path.join(RESULTS_DIR, "data_inventory.json"))
    print("saved", os.path.join(RESULTS_DIR, "splits.json"))


if __name__ == "__main__":
    main()